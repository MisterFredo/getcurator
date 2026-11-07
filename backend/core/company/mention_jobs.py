"""Durable server queue for global and individual external-mention passages.

GCS only for orchestration. One runner per dataset; all browser mutations enqueue.
"""
from __future__ import annotations
from datetime import datetime,timezone,timedelta
import hashlib
import json
import uuid
from fastapi import HTTPException
from google.api_core.exceptions import NotFound, PreconditionFailed
from core.company import mention_service as engine
from core.company.mention_watch_service import list_mention_watch_companies,require_mention_watch_enabled
from core.library import company_watch_library as lib
from utils.gcs import bucket

ROOT=f'{engine.ROOT}/server-queue-v3'
TERMINAL={'COMPLETE','PARTIAL','FAILED','SKIPPED'}


def now():return datetime.now(timezone.utc)
def stamp():return now().isoformat()
def _path(job):
    try:uuid.UUID(job)
    except (ValueError,TypeError):raise ValueError('Identifiant de lot invalide')
    return f'{ROOT}/jobs/{job}.json'


def _read(path,default=None):
    for _ in range(3):
        blob=bucket.blob(path)
        try:blob.reload()
        except NotFound:return default
        generation=int(blob.generation)
        try:return json.loads(bucket.blob(path,generation=generation).download_as_text(if_generation_match=generation))
        except (NotFound,PreconditionFailed):continue
    raise HTTPException(409,'État momentanément indisponible ; actualisez')


def _put(path,value):
    blob=bucket.blob(path);blob.cache_control='private, no-store, max-age=0'
    blob.upload_from_string(json.dumps(value,ensure_ascii=False),content_type='application/json')


def _lock():return lib.document_lock('mention-queue-'+hashlib.sha256(lib.BASE.encode()).hexdigest())
def _index():return _read(f'{ROOT}/index.json',{'jobs':[],'reservations':{}})


def read_job(job):
    result=_read(_path(job))
    if result is None:raise HTTPException(404,'Lot de collecte introuvable')
    return result


def _summary(job):
    rows=job['companies']
    return {key:job.get(key) for key in ('id_job','kind','status','created_at','updated_at','scheduled_for')}|{
        'total':len(rows),'finished':sum(r['status'] in TERMINAL for r in rows),
        'new_mentions':sum(r.get('progress',{}).get('new_mentions',0) for r in rows),
        'failed':sum(r['status']=='FAILED' for r in rows),
        'current_company':next((r['name'] for r in rows if r['status']=='RUNNING'),None)}


def _save_job(index,job):
    job['updated_at']=stamp()
    rows=job['companies']
    if all(row['status'] in TERMINAL for row in rows):
        job['status']='PARTIAL' if any(r['status'] in {'PARTIAL','FAILED'} for r in rows) else 'COMPLETE'
    else:job['status']='RUNNING' if any(r['status'] in ('RUNNING','WAITING') for r in rows) else 'QUEUED'
    _put(_path(job['id_job']),job)
    summaries=[_summary(job) if j['id_job']==job['id_job'] else j for j in index['jobs']]
    if not any(j['id_job']==job['id_job'] for j in summaries):summaries.append(_summary(job))
    active=[j for j in summaries if j['status'] not in TERMINAL]
    history=sorted((j for j in summaries if j['status'] in TERMINAL),key=lambda j:j['created_at'],reverse=True)[:50]
    index['jobs']=active+history
    _put(f'{ROOT}/index.json',index)


def _options(data):
    return {'max_pages':getattr(data,'max_pages',3),'search_budget_seconds':getattr(data,'search_budget_seconds',90),
        'max_candidates':getattr(data,'max_candidates',1000),'excluded_domains':list(getattr(data,'excluded_domains',[]))}


def _reservation(index,company):
    jobid=index['reservations'].get(company)
    if not jobid:return None,None
    job=_read(_path(jobid))
    row=next((r for r in (job or {}).get('companies',[]) if r['id_company']==company and r['status'] not in TERMINAL),None)
    if row:return job,row
    index['reservations'].pop(company,None)
    return None,None


def _row(company,options,run=None,action='COLLECT',workers=1):
    return {'id_company':company['id_company'],'name':company['name'],'status':'PENDING',
        'id_run':run or str(uuid.uuid4()),'action':action,'action_started':False,
        'options':options,'search_workers':workers,'attempts':0,'progress':{}}


def launch_global(data=None,*,schedule_slot=None):
    companies=list_mention_watch_companies()
    if not companies:raise HTTPException(400,'Aucune société active éligible à la veille Mentions')
    with _lock():
        index=_index()
        config=None
        if schedule_slot is not None:
            config=get_schedule()
            if not config['is_enabled'] or config.get('next_at')!=schedule_slot:return None
            for summary in index['jobs']:
                if summary.get('scheduled_for')==schedule_slot:
                    existing=read_job(summary['id_job']);_advance_schedule(config,existing);return {**_summary(existing),'reused':True}
        for summary in index['jobs']:
            if summary.get('kind')=='GLOBAL' and summary['status'] not in TERMINAL:
                job=read_job(summary['id_job'])
                if job['status'] not in TERMINAL:
                    if config is not None:_advance_schedule(config,job)
                    return {**_summary(job),'reused':True}
        job={'id_job':str(uuid.uuid4()),'kind':'GLOBAL','status':'QUEUED','created_at':stamp(),'scheduled_for':schedule_slot,'companies':[]}
        for company in companies:
            other,_=_reservation(index,company['id_company'])
            row=_row(company,_options(data))
            if other:row.update(status='SKIPPED',message='Déjà prévu dans un autre lot',other_job=other['id_job'])
            else:index['reservations'][company['id_company']]=job['id_job']
            job['companies'].append(row)
        _save_job(index,job)
        if config is not None:_advance_schedule(config,job)
        return {**_summary(job),'reused':False}


def launch_company(company,data=None,*,run=None,action='COLLECT',workers=1):
    config=require_mention_watch_enabled(company)
    with _lock():
        index=_index();existing,row=_reservation(index,company)
        if existing:
            # An individual request moves its pending company to the front of
            # the global lot rather than creating a competing passage.
            if row['status']=='RUNNING':return {**_summary(existing),'reused':True,'company_running':company}
            row['priority_requested']=True
            if run and row['status']=='PENDING':row.update(id_run=run,action=action,search_workers=workers)
            _save_job(index,existing)
            return {**_summary(existing),'reused':True,'prioritized_company':company}
        job={'id_job':str(uuid.uuid4()),'kind':'INDIVIDUAL','status':'QUEUED','created_at':stamp(),
            'companies':[_row({'id_company':company,'name':config['company_name']},_options(data),run,action,workers)]}
        index['reservations'][company]=job['id_job'];_save_job(index,job)
        return {**_summary(job),'reused':False}


def enqueue_existing(run,action='CONTINUE',workers=1):
    state=engine.read(run)
    if state.get('search_scope')!='NEWS':raise HTTPException(409,'Lancer une nouvelle collecte News')
    if action in ('CONTINUE','RETRY_SEARCHES') and state.get('engine_version')!=engine.ENGINE_VERSION:
        raise HTTPException(409,'Lancer une nouvelle collecte avec le moteur actuel')
    if action=='RETRY_SEARCHES' and not state.get('deferred_searches') and not any(not error.get('resolved') for error in state.get('search_errors',[])):
        raise HTTPException(409,'Aucune recherche à compléter dans ce passage')
    if action=='CONTINUE' and state['status'] in ('COMPLETE','PARTIAL'):
        raise HTTPException(409,'Ce passage est terminé ; lancer un nouveau passage')
    if action in ('RECHECK','RETRY_SEARCHES') and state['status'] not in ('COMPLETE','PARTIAL'):
        raise HTTPException(409,'Terminer ce passage avant réexamen')
    if workers not in (1,4):raise ValueError('Choisir 1 ou 4 appels simultanés')
    return launch_company(state['id_company'],run=run,action=action,workers=workers)


def reject_browser_step(run):
    raise HTTPException(409,'La collecte est exécutée côté serveur. Actualisez la page ou utilisez Reprendre côté serveur.')


def list_jobs():
    index=_index();health=_read(f'{ROOT}/heartbeat.json',{})
    recent=False
    if health.get('at'):
        try:recent=(now()-datetime.fromisoformat(health['at'])).total_seconds()<90
        except ValueError:pass
    return {'jobs':sorted(index['jobs'],key=lambda j:j['created_at'],reverse=True),'schedule':get_schedule(),
        'worker':{'available':recent,'last_seen_at':health.get('at')}}


def heartbeat():_put(f'{ROOT}/heartbeat.json',{'at':stamp()})


def claim_work(token):
    with _lock():
        index=_index();jobs=[]
        for summary in index['jobs']:
            if summary['status'] not in TERMINAL:
                job=read_job(summary['id_job'])
                if job['status'] in TERMINAL:_save_job(index,job)
                else:jobs.append(job)
        candidates=[]
        for job in jobs:
            for pos,row in enumerate(job['companies']):
                if row['status'] in TERMINAL:continue
                if row.get('retry_after') and datetime.fromisoformat(row['retry_after'])>now():continue
                priority=0 if row['status'] in ('RUNNING','WAITING') else 1 if row.get('priority_requested') else 2 if job['kind']=='INDIVIDUAL' else 3
                candidates.append((priority,job['created_at'],pos,job,row))
        if not candidates:return None
        _,_,_,job,row=min(candidates,key=lambda item:item[:3])
        if row['status']=='RUNNING' and row.get('claim_token')==token:return {'id_job':job['id_job'],'row':dict(row)}
        row.update(status='RUNNING',claim_token=token)
        row.setdefault('started_at',stamp())
        _save_job(index,job)
        return {'id_job':job['id_job'],'row':dict(row)}


def progress(state):
    return {'stage':state['status'],'new_mentions':sum(r['status']=='IMPORTED' for r in state['results']),
        'known_urls':sum(r['status']=='KNOWN' for r in state.get('resolutions',[])),
        'search_requests':sum(v['requests'] for v in state.get('coverage',{}).values()),
        'raw_urls':len(state['candidates']),'resolved':len(state.get('resolutions',[])),
        'examined':len(state['results']),'pages':len(state.get('resolved_candidates',[])),
        'warnings':len(state['warnings']),'timings':state.get('timings',{})}


def finish_work(work,token,*,state=None,error=None,skipped=False):
    with _lock():
        index=_index();job=read_job(work['id_job'])
        row=next(r for r in job['companies'] if r['id_company']==work['row']['id_company'])
        if row.get('claim_token')!=token:return False
        row['eligibility_checked']=work['row'].get('eligibility_checked',False)
        if state is not None:
            row.update(progress=progress(state),action_started=True,attempts=0)
            row.pop('error',None);row.pop('retry_after',None)
            row['status']=state['status'] if state['status'] in ('COMPLETE','PARTIAL') else 'RUNNING'
        elif skipped:row.update(status='SKIPPED',error=str(error))
        elif error is not None:
            # Locks are short-lived contention, not a reason to lose a run.
            locked=isinstance(error,HTTPException) and error.status_code==409
            row['attempts']=row.get('attempts',0)+(0 if locked else 1)
            row['error']=str(error.detail) if isinstance(error,HTTPException) else type(error).__name__
            if not locked and row['attempts']>=3:row['status']='FAILED'
            else:
                row['status']='WAITING'
                row['retry_after']=(now()+timedelta(seconds=30 if locked else min(120,30*row['attempts']))).isoformat()
        if row['status'] in TERMINAL:
            row['finished_at']=stamp()
            if index['reservations'].get(row['id_company'])==job['id_job']:index['reservations'].pop(row['id_company'],None)
        _save_job(index,job)
        return True


def get_schedule():
    return _read(f'{ROOT}/schedule.json',{'is_enabled':False,'interval_hours':24,'next_at':None,
        'options':{'max_pages':3,'search_budget_seconds':90,'max_candidates':1000,'excluded_domains':[]}})


def save_schedule(data):
    with _lock():
        previous=get_schedule()
        value={'is_enabled':data.is_enabled,'interval_hours':data.interval_hours,'options':_options(data),
            'updated_at':stamp(),'last_job_id':previous.get('last_job_id'),'last_enqueued_at':previous.get('last_enqueued_at')}
        if data.is_enabled:
            unchanged=previous.get('is_enabled') and previous.get('interval_hours')==data.interval_hours
            value['next_at']=previous.get('next_at') if unchanged and previous.get('next_at') else (now()+timedelta(hours=data.interval_hours)).isoformat()
        else:value['next_at']=None
        _put(f'{ROOT}/schedule.json',value)
        return value


def _advance_schedule(config,job):
    config.update(next_at=(now()+timedelta(hours=config['interval_hours'])).isoformat(),
        last_enqueued_at=stamp(),last_job_id=job['id_job'])
    config.pop('last_error',None);config.pop('retry_after',None)
    _put(f'{ROOT}/schedule.json',config)


def maybe_schedule():
    config=get_schedule()
    if not config.get('is_enabled') or not config.get('next_at'):return None
    if datetime.fromisoformat(config['next_at'])>now():return None
    if config.get('retry_after') and datetime.fromisoformat(config['retry_after'])>now():return None
    from types import SimpleNamespace
    try:return launch_global(SimpleNamespace(**config['options']),schedule_slot=config['next_at'])
    except Exception as exc:
        with _lock():
            latest=get_schedule()
            if latest.get('next_at')==config['next_at'] and latest.get('is_enabled'):
                latest.update(last_error=str(exc.detail) if isinstance(exc,HTTPException) else type(exc).__name__,
                    retry_after=(now()+timedelta(minutes=5)).isoformat())
                _put(f'{ROOT}/schedule.json',latest)
        return None
