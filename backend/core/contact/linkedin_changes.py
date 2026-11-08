"""Explicit LinkedIn comparison approvals; reuse Contact's atomic affiliation/watch update."""
from __future__ import annotations
import json
import logging
import time
import uuid
from datetime import datetime, timezone
from fastapi import HTTPException
from api.contact.models import ContactUpdate,linkedin_profile
from core.contact import service as contacts

log=logging.getLogger(__name__)

def imports():
    from core.contact import linkedin_import
    return linkedin_import

def timestamp(value):
    if isinstance(value,str):value=datetime.fromisoformat(value.replace('Z','+00:00'))
    return value.replace(tzinfo=value.tzinfo or timezone.utc).isoformat()

def current_indexes(rows):
    urls={};emails={}
    for raw in rows:
        person=contacts.out(raw)
        if person.get('updated_at'):person['updated_at']=timestamp(person['updated_at'])
        try:url=linkedin_profile(person.get('linkedin_url'))
        except ValueError:url=None
        if url:urls.setdefault(url,[]).append(person)
        if person.get('email'):emails.setdefault(person['email'].strip().casefold(),[]).append(person)
    return urls,emails

def annotate(row,urls,emails):
    matches=urls.get(row['linkedin_url'],[])
    email_matches=emails.get((row.get('email') or '').casefold(),[])
    row['existing']=bool(matches or email_matches)
    row['current']=None;row['identity_conflict']=None
    if len(matches)>1:row['identity_conflict']='Plusieurs contacts partagent ce profil ; rapprochement manuel requis.'
    elif len(matches)==1:
        current=matches[0]
        if any(p['id_contact']!=current['id_contact'] for p in email_matches):
            row['identity_conflict']='Cet e-mail appartient à un autre contact ; vérifier les fiches.'
        else:
            keys=['id_contact','display_name','id_company','company_name','job_title','email','updated_at','linkedin_follow_enabled','is_active']
            row['current']={k:current.get(k) for k in keys}
    elif email_matches:
        row['identity_conflict']='E-mail déjà présent avec un autre profil LinkedIn ; vérifier les fiches.'
    return row

def changes(row,current,company_id,fields,continue_follow=False):
    """Only approved nonempty fields. Never change names, profile identity or active state."""
    m=imports();patch={}
    if 'company' in fields and company_id and company_id!=current.get('id_company'):
        if continue_follow and not (current.get('linkedin_follow_enabled') and current.get('is_active')):
            raise HTTPException(422,'La poursuite du suivi nécessite un contact déjà suivi et actif')
        patch['id_company']=company_id
        patch['linkedin_follow_enabled']=bool(continue_follow)
    if 'job_title' in fields and row.get('job_title') and m.normalized(row['job_title'])!=m.normalized(current.get('job_title')):
        patch['job_title']=row['job_title']
    if 'email' in fields and row.get('email') and row['email'].casefold()!=(current.get('email') or '').casefold():
        patch['email']=row['email']
    return patch

def summary(job):
    items=job.get('items',[])
    counts={status:sum(i['status']==status for i in items) for status in ['PENDING','APPLIED','ALREADY_CURRENT','CONFLICT','ERROR']}
    status=job['status']
    if status=='RUNNING' and time.time()-datetime.fromisoformat(job['updated_at']).timestamp()>180:status='INTERRUPTED'
    return {'id_job':job['id_job'],'status':status,'total':len(items),'counts':counts,'error':job.get('error'),
            'items':[{'contact_key':i['contact_key'],'name':i['name'],'status':i['status'],'message':i.get('message')} for i in items]}

def persist(run,job):
    m=imports();job['updated_at']=m.now();run['change_job']=job;m.save(run)

def reserve(run_id,payload):
    m=imports()
    with m.lock(run_id):
        run=m.read(run_id)
        if run['status'] not in ('READY','IMPORTED'):raise HTTPException(409,'Terminer la récupération ou l’import avant les mises à jour')
        old=run.get('change_job')
        if old and old.get('request_id')==payload.request_id:return {'id_run':run_id,'queued':False,'change_job':summary(old)}
        if old and old['status']=='RUNNING':raise HTTPException(409,'Des mises à jour sont déjà en cours ; attendre ou reprendre leur traitement')
        raw_rows,_=m.candidates(run['rows']);by_key={r['key']:r for r in raw_rows}
        urls,emails=current_indexes(contacts.query(contacts.READ))
        companies,_,_=m.directory();active={c['ID_COMPANY'] for c in companies}
        from core.contact import linkedin_company_rules
        ignored={key for key,value in linkedin_company_rules.rules().items() if value=='IGNORE'}
        seen=set();groups={};items=[]
        for approval in payload.approvals:
            row=by_key.get(approval.contact_key)
            if not row:raise HTTPException(400,'Contact absent de cet aperçu')
            if row['group_key'] in ignored:raise HTTPException(409,'Société ignorée ; la rétablir avant de valider ses évolutions')
            annotate(row,urls,emails);current=row['current']
            if row['identity_conflict'] or not current or current['id_contact']!=approval.id_contact:
                raise HTTPException(409,'Identité du contact ambiguë ; actualiser et vérifier sa fiche')
            if current['id_contact'] in seen:raise HTTPException(400,'Contact sélectionné plusieurs fois')
            seen.add(current['id_contact'])
            if row['group_key'] in groups and groups[row['group_key']]!=approval.id_company:raise HTTPException(400,'Rapprochements contradictoires pour un même libellé société')
            groups[row['group_key']]=approval.id_company
            if approval.id_company not in active:raise HTTPException(409,'Rapprocher le libellé d’une société GetCurator active avant de valider')
            if timestamp(approval.expected_updated_at)!=current['updated_at']:
                raise HTTPException(409,'Une fiche a changé depuis l’aperçu ; actualiser avant de valider')
            patch=changes(row,current,approval.id_company,approval.fields,approval.continue_follow)
            if not patch:continue
            items.append({'contact_key':row['key'],'id_contact':current['id_contact'],'name':current.get('display_name') or '',
              'linkedin_url':row['linkedin_url'],'expected_updated_at':current['updated_at'],'patch':patch,
              'company_key':row['group_key'],'company_label':row['company_label'],'mapped_company':approval.id_company,
              'status':'PENDING'})
        if not items:raise HTTPException(400,'Aucune différence sélectionnée à mettre à jour')
        # Preserve completed approvals as separate private audit objects.
        if old:
            b=m.blob('changes-'+old['id_job']);b.cache_control='no-store'
            b.upload_from_string(json.dumps(old,ensure_ascii=False),content_type='application/json')
        job={'id_job':str(uuid.uuid4()),'request_id':payload.request_id,'status':'RUNNING','updated_at':m.now(),'items':items,'error':None}
        persist(run,job)
        return {'id_run':run_id,'queued':True,'change_job':summary(job)}

def resume(run_id):
    m=imports()
    with m.lock(run_id):
        run=m.read(run_id);job=run.get('change_job')
        if not job:raise HTTPException(404,'Aucune mise à jour à reprendre')
        if job['status']=='RUNNING' and summary(job)['status']!='INTERRUPTED':return {'id_run':run_id,'queued':False}
        if not any(i['status'] in ('PENDING','ERROR') for i in job['items']):raise HTTPException(409,'Aucune mise à jour à reprendre ; actualiser pour comparer à nouveau')
        for item in job['items']:
            if item['status']=='ERROR':item['status']='PENDING'
        job['status']='RUNNING';job['error']=None;persist(run,job)
        return {'id_run':run_id,'queued':True}

def remember(items):
    m=imports();maps={i['company_key']:{'key':i['company_key'],'label':i['company_label'],'company':i['mapped_company']} for i in items if i['status'] in ('APPLIED','ALREADY_CURRENT') and i['company_label'].strip()}
    if not maps:return
    # Separate memory write: it must never roll back an already approved identity update.
    with contacts.scope_lock():
        contacts.query(f'''MERGE `{m.MAP}` T USING (
          SELECT JSON_VALUE(j,'$.key') COMPANY_KEY,JSON_VALUE(j,'$.label') LINKEDIN_LABEL,JSON_VALUE(j,'$.company') ID_COMPANY
          FROM UNNEST(JSON_QUERY_ARRAY(PARSE_JSON(@maps))) j) S ON T.COMPANY_KEY=S.COMPANY_KEY
          WHEN MATCHED THEN UPDATE SET ID_COMPANY=S.ID_COMPANY,LINKEDIN_LABEL=S.LINKEDIN_LABEL,UPDATED_AT=CURRENT_TIMESTAMP()
          WHEN NOT MATCHED THEN INSERT(COMPANY_KEY,LINKEDIN_LABEL,ID_COMPANY,CREATED_AT,UPDATED_AT)
          VALUES(S.COMPANY_KEY,S.LINKEDIN_LABEL,S.ID_COMPANY,CURRENT_TIMESTAMP(),CURRENT_TIMESTAMP())''',
          [contacts.p('maps','STRING',json.dumps(list(maps.values()),ensure_ascii=False))])

def apply(run_id):
    m=imports()
    with m.lock(run_id):
        run=m.read(run_id);job=run.get('change_job')
        if not job or job['status']!='RUNNING':return
        began=time.monotonic()
        try:
            for item in job['items']:
                if item['status']!='PENDING':continue
                if time.monotonic()-began>m.MAX_SECONDS:
                    job['status']='PARTIAL';job['error']='UPDATE_TIME_BUDGET';persist(run,job);return
                try:
                    current=contacts.get_contact(item['id_contact'])
                    if item['patch'].get('id_company'):
                        target=contacts.query(f'SELECT IS_ACTIVE FROM `{contacts.COMPANY}` WHERE ID_COMPANY=@company',[contacts.p('company','STRING',item['patch']['id_company'])])
                        if not target or not target[0]['IS_ACTIVE']:raise HTTPException(409,'La société cible est absente ou inactive ; nouvelle comparaison nécessaire')
                    if linkedin_profile(current.get('linkedin_url'))!=item['linkedin_url']:
                        raise HTTPException(409,'Le profil du contact a changé ; nouvelle comparaison nécessaire')
                    if all(current.get(k)==v for k,v in item['patch'].items()):
                        # Crash after commit but before checkpoint: no second identity/watch mutation.
                        item['status']='ALREADY_CURRENT'
                    else:
                        payload=ContactUpdate(**item['patch'],expected_updated_at=item['expected_updated_at'])
                        contacts.update_contact(item['id_contact'],payload)
                        item['status']='APPLIED'
                    item['message']=None
                except HTTPException as exc:
                    item['status']='CONFLICT' if exc.status_code in (400,404,409,422) else 'ERROR'
                    item['message']=str(exc.detail)[:500]
                except Exception:
                    log.exception('LinkedIn contact update failed: %s',item['id_contact'])
                    item['status']='ERROR';item['message']='Écriture interrompue ; réessayer ou consulter les logs.'
                persist(run,job)
            try:remember(job['items'])
            except Exception:
                log.exception('LinkedIn company mapping memory failed: %s',run_id)
                job['error']='UPDATE_MAPPING_MEMORY_FAILED'
            job['status']='PARTIAL' if any(i['status']=='ERROR' for i in job['items']) else 'COMPLETE'
            persist(run,job)
        except Exception:
            log.exception('LinkedIn changes interrupted: %s',run_id)
            job['status']='PARTIAL';job['error']='UPDATE_INTERRUPTED';persist(run,job)
