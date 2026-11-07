"""Manual, resumable media collection in the existing API process. No scheduler."""
from __future__ import annotations
import hashlib
import json
import logging
import threading
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone, timedelta
from fastapi import HTTPException
from google.api_core.exceptions import NotFound, PreconditionFailed
from config import BQ_PROJECT, BQ_DATASET
from utils.gcs import bucket
from utils.bigquery_utils import query_bq
from core.library.company_watch_library import document_lock
from core.discovery.service import scan_source
from core.discovery.linkedin_brightdata_service import scan as linkedin_scan

log=logging.getLogger(__name__)
BASE=f'{BQ_PROJECT}.{BQ_DATASET}'
ROOT='cockpit-media/'+hashlib.sha256(BASE.encode()).hexdigest()
TERMINAL={'COMPLETE','FAILED'}
MANUAL={'MANUAL','PDF_MANUAL','NEWSLETTER_MANUAL','LINKEDIN_PROFILE'}

def now():return datetime.now(timezone.utc)
def stamp():return now().isoformat()
def read(path,default=None):
    for _ in range(3):
        b=bucket.blob(ROOT+'/'+path)
        try:b.reload()
        except NotFound:return default
        generation=int(b.generation)
        try:return json.loads(bucket.blob(b.name,generation=generation).download_as_text(if_generation_match=generation))
        except (NotFound,PreconditionFailed):continue
    raise HTTPException(409,'Suivi momentanément indisponible')
def write(path,value):
    b=bucket.blob(ROOT+'/'+path);b.cache_control='private, no-store, max-age=0'
    b.upload_from_string(json.dumps(value,ensure_ascii=False),content_type='application/json')
def lock():return document_lock('cockpit-media-'+hashlib.sha256(BASE.encode()).hexdigest())
def job_path(job):
    try:uuid.UUID(job)
    except (ValueError,TypeError):raise HTTPException(400,'Identifiant de collecte invalide')
    return 'jobs/'+job+'.json'
def get_job(job):
    value=read(job_path(job))
    if value is None:raise HTTPException(404,'Collecte introuvable')
    return value

def launch(scope):
    if scope not in {'ALL','WEB','LINKEDIN'}:raise HTTPException(400,'Périmètre invalide')
    with lock():
        index=read('index.json',{'jobs':[]})
        for key in index['jobs']:
            old=get_job(key)
            if old['status'] not in {'COMPLETE','PARTIAL'}:
                if old['scope']!=scope:raise HTTPException(409,'Une collecte Médias est déjà active ; reprendre son suivi avant un autre périmètre')
                return {**old,'reused':True}
        sources=query_bq(f"SELECT SOURCE_ID, NAME, ACQUISITION_MODE FROM `{BASE}.RATECARD_SOURCE` WHERE NULLIF(TRIM(DOMAIN),'') IS NOT NULL")
        unique={}
        for s in sources:
            mode=(s.get('ACQUISITION_MODE') or '').upper()
            if not mode or mode in MANUAL:continue
            linked=mode=='LINKEDIN_BRIGHTDATA'
            if scope=='WEB' and linked or scope=='LINKEDIN' and not linked:continue
            unique[s['SOURCE_ID']]={'id_source':s['SOURCE_ID'],'name':s['NAME'],'linkedin':linked,'status':'PENDING','new':0}
        if not unique:raise HTTPException(400,'Aucune source automatique dans ce périmètre')
        job={'id_job':str(uuid.uuid4()),'scope':scope,'status':'RUNNING','created_at':stamp(),'updated_at':stamp(),'sources':list(unique.values())}
        write(job_path(job['id_job']),job);index['jobs']=([job['id_job']]+index['jobs'])[:30];write('index.json',index)
        return {**job,'reused':False}

def list_jobs():
    # Only one active media passage is permitted; the latest is the cockpit
    # follow-up. Historical jobs remain readable by ID without replaying their
    # full source lists at every refresh.
    return {'jobs':[get_job(k) for k in read('index.json',{'jobs':[]})['jobs'][:1]]}

class Lease:
    def __init__(self):self.token=str(uuid.uuid4());self.generation=None;self.expiry=now();self.stop=threading.Event();self.lost=False;self.thread=None
    @property
    def valid(self):return self.generation is not None and not self.lost and now()<self.expiry
    def save(self,generation):
        self.expiry=now()+timedelta(minutes=5)
        b=bucket.blob(ROOT+'/lease.json')
        b.upload_from_string(json.dumps({'owner':self.token,'expires':self.expiry.isoformat()}),content_type='application/json',if_generation_match=generation)
        self.generation=int(b.generation)
    def renew(self):
        while not self.stop.wait(30):
            try:self.save(self.generation)
            except Exception:self.lost=True;log.exception('Media lease renewal failed');return
    def __enter__(self):
        b=bucket.blob(ROOT+'/lease.json');expected=0
        try:
            b.reload();expected=int(b.generation)
            value=json.loads(bucket.blob(b.name,generation=expected).download_as_text(if_generation_match=expected))
            if datetime.fromisoformat(value['expires'])>now():return self
        except NotFound:pass
        except PreconditionFailed:return self
        try:self.save(expected)
        except PreconditionFailed:return self
        self.thread=threading.Thread(target=self.renew,daemon=True);self.thread.start();return self
    def __exit__(self,*args):
        self.stop.set()
        if self.thread:self.thread.join(timeout=2)
        if self.generation is not None:
            try:bucket.blob(ROOT+'/lease.json').delete(if_generation_match=self.generation)
            except (NotFound,PreconditionFailed):pass

def step_source(row):
    result=dict(row)
    try:
        if row['linkedin']:
            response=linkedin_scan(row['id_source'],start=row['status']=='PENDING')
            status=response['status']
            if status in {'RUNNING','STARTING'}:
                result.update(status='RUNNING',next_poll=(now()+timedelta(seconds=10)).isoformat())
                result.setdefault('started_at',stamp())
                if now()-datetime.fromisoformat(result['started_at'])>timedelta(minutes=30):
                    result.update(status='FAILED',error='Attente fournisseur supérieure à 30 minutes ; une nouvelle collecte reprendra le résultat existant')
            elif status in {'COMPLETE','ok'}:result.update(status='COMPLETE',new=response.get('discovered_urls',0),warnings=response.get('warnings',[]))
            else:result.update(status='FAILED',error=response.get('message') or status)
        else:
            response=scan_source(row['id_source']);result.update(status='COMPLETE',new=response.get('discovered_urls',0))
    except Exception as exc:
        log.exception('Media collection failed source=%s',row['id_source'])
        # A network error may have left a paid LinkedIn job running. Never restart
        # within this passage; a subsequent passage reuses the provider snapshot.
        result.update(status='FAILED',error=str(exc.detail) if isinstance(exc,HTTPException) else str(exc))
    return result

def drain():
    """Finite queue drain, started only by an explicit POST."""
    pause=threading.Event()
    try:
        while True:
            active=next((j for j in list_jobs()['jobs'] if j['status']=='RUNNING'),None)
            if active is None:return
            with Lease() as lease:
                if not lease.valid:pause.wait(3);continue
                while lease.valid:
                    job=get_job(active['id_job'])
                    pending=[r for r in job['sources'] if r['status'] not in TERMINAL]
                    if not pending:break
                    # Keep at most three LinkedIn accounts active at once.
                    running=[r for r in pending if r['status']=='RUNNING']
                    due=[r for r in running if not r.get('next_poll') or datetime.fromisoformat(r['next_poll'])<=now()]
                    capacity=max(0,3-len(running))
                    due+= [r for r in pending if r['status']=='PENDING'][:capacity]
                    if not due:pause.wait(1);continue
                    with ThreadPoolExecutor(max_workers=3) as pool:updates=list(pool.map(step_source,due[:3]))
                    if not lease.valid:return
                    with lock():
                        latest=get_job(job['id_job']);mapped={r['id_source']:r for r in updates}
                        latest['sources']=[mapped.get(r['id_source'],r) for r in latest['sources']]
                        latest['updated_at']=stamp()
                        if all(r['status'] in TERMINAL for r in latest['sources']):latest['status']='PARTIAL' if any(r['status']=='FAILED' for r in latest['sources']) else 'COMPLETE'
                        write(job_path(job['id_job']),latest)
                    if latest['status']!='RUNNING':break
    except Exception:log.exception('Media execution interrupted; progress preserved for manual resume')
