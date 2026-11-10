"""Manually triggered backend queue for company watch. No cron or external worker."""
from __future__ import annotations
import hashlib
import json
import logging
import threading
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone, timedelta
from fastapi import HTTPException
from google.api_core.exceptions import NotFound, PreconditionFailed
from core.company import watch_monitoring as monitoring
from core.library.company_watch_library import document_lock
from utils.gcs import bucket

log = logging.getLogger(__name__)
TERMINAL = {'COMPLETE', 'FAILED', 'SKIPPED'}
ROOT = monitoring.ROOT
load, save, stamp = monitoring.load, monitoring.save, monitoring.stamp

def now(): return datetime.now(timezone.utc)
def lock(): return document_lock('watch-operations-' + hashlib.sha256(ROOT.encode()).hexdigest())
def path(job_id):
    try: uuid.UUID(job_id)
    except (TypeError, ValueError): raise HTTPException(400, 'Identifiant de collecte invalide')
    return 'jobs/' + job_id + '.json'
def get_job(job_id):
    value = load(path(job_id))
    if value is None: raise HTTPException(404, 'Collecte introuvable')
    return value

def list_jobs(company_id=None, watch_id=None):
    for job_id in load('index.json', {'jobs': []})['jobs']:
        job = get_job(job_id)
        if company_id and not (job.get('id_company') == company_id or any(s['id_company'] == company_id for s in job['sources'])): continue
        if watch_id and not any(s['id_company_watch'] == watch_id for s in job['sources']): continue
        return {'jobs': [job]}
    return {'jobs': []}

def source_signature(watch):
    return hashlib.sha256(json.dumps({k: watch.get(k) for k in
        ('source_url', 'collection_method', 'collection_config')}, sort_keys=True, default=str).encode()).hexdigest()

def all_sources(company_id=None, watch_id=None):
    from core.company import watch_service
    if watch_id:
        if not company_id: raise HTTPException(400, 'Société obligatoire pour un point individuel')
        return [watch_service.get_company_watch(company_id, watch_id)]
    result, offset = [], 0
    while True:
        response = watch_service.list_company_watch(id_company=company_id, is_active=True, limit=500, offset=offset)
        result.extend(response['watches'])
        if not response['has_more']: return result
        offset += 500

def launch(kind='PUBLICATIONS', channel='ALL', company_id=None, watch_id=None, failed_only=False, recover_only=False, role='ALL'):
    if kind not in {'ALL', 'SINGLE_PAGE', 'PUBLICATIONS'} or channel not in {'ALL', 'WEB', 'LINKEDIN'}:
        raise HTTPException(400, 'Périmètre invalide')
    if role not in {'ALL','CORPORATE','EMPLOYEE'}: raise HTTPException(400, 'Origine invalide')
    scope = dict(role=role, kind=kind, channel=channel, id_company=company_id, id_company_watch=watch_id,
                 failed_only=failed_only, recover_only=recover_only)
    with lock():
        index = load('index.json', {'jobs': []})
        for old_id in index['jobs'][:1]:
            old = get_job(old_id)
            if old['status'] == 'PAUSED':
                raise HTTPException(409, 'Une collecte Veille est suspendue ; reprendre son suivi avant un autre lancement')
            if old['status'] == 'RUNNING':
                if all(old.get(k) == v for k, v in scope.items()): return {**old, 'reused': True}
                raise HTTPException(409, 'Une collecte Veille est déjà active ; consulter ou reprendre son suivi avant un autre lancement')
        sources = []
        eligible = []
        for watch in all_sources(company_id, watch_id):
            ch, ty = monitoring.classify(watch)
            source_role = 'EMPLOYEE' if watch.get('id_contact') or watch.get('source_role')=='EMPLOYEE' else 'CORPORATE'
            if role!='ALL' and source_role!=role: continue
            if not watch.get('is_active') or watch['collection_method'] not in {'HTML', 'BRIGHTDATA'} or watch['source_type'] == 'PDF': continue
            if channel != 'ALL' and ch != channel or kind != 'ALL' and ty != kind: continue
            if recover_only and watch['collection_method'] != 'BRIGHTDATA': continue
            eligible.append(watch)
        if failed_only:
            # GCS reads only; no BigQuery request or provider call per contact.
            with ThreadPoolExecutor(max_workers=8) as pool: checks = list(pool.map(monitoring.diagnostic, eligible))
            eligible = [w for w, state in zip(eligible, checks) if state and state.get('status') == 'FAILED']
        for watch in eligible:
            ch, ty = monitoring.classify(watch)
            sources.append({'id_company': watch['id_company'], 'id_company_watch': watch['id_company_watch'],
                'source_role': 'EMPLOYEE' if watch.get('id_contact') or watch.get('source_role')=='EMPLOYEE' else 'CORPORATE',
                'label': watch['label'], 'company_name': watch.get('company_name'), 'channel': ch, 'kind': ty,
                'method': watch['collection_method'], 'signature': source_signature(watch),
                'status': 'PENDING', 'new': 0, 'known': 0, 'unchanged': 0,
                'retry': failed_only, 'recover_only': recover_only})
        if not sources: raise HTTPException(400, 'Aucune source active correspondante' + (' en échec connu' if failed_only else ''))
        job = {**scope, 'id_job': str(uuid.uuid4()), 'status': 'RUNNING', 'created_at': stamp(),
               'updated_at': stamp(), 'sources': sources}
        save(path(job['id_job']), job)
        index['jobs'] = ([job['id_job']] + index['jobs'])[:30]
        save('index.json', index)
        return {**job, 'reused': False}

def pause(job_id):
    with lock():
        job = get_job(job_id)
        if job['status'] == 'RUNNING':
            job.update(status='PAUSED', updated_at=stamp())
            save(path(job_id), job)
        return job

def resume(job_id):
    with lock():
        job = get_job(job_id)
        if job['status'] == 'PAUSED':
            job.update(status='RUNNING', updated_at=stamp())
            save(path(job_id), job)
        return job

class Lease:
    def __init__(self):
        self.token = str(uuid.uuid4()); self.generation = None; self.expiry = now()
        self.stop = threading.Event(); self.lost = False; self.thread = None
    @property
    def valid(self): return self.generation is not None and not self.lost and now() < self.expiry
    def write(self, generation):
        expiry = now() + timedelta(minutes=5)
        b = bucket.blob(ROOT + '/lease.json')
        b.upload_from_string(json.dumps({'owner': self.token, 'expires': expiry.isoformat()}),
            content_type='application/json', if_generation_match=generation)
        self.generation = int(b.generation); self.expiry = expiry
    def renew(self):
        while not self.stop.wait(30):
            try: self.write(self.generation)
            except Exception: self.lost = True; log.exception('Watch lease lost'); return
    def __enter__(self):
        b = bucket.blob(ROOT + '/lease.json'); generation = 0
        try:
            b.reload(); generation = int(b.generation)
            value = json.loads(bucket.blob(b.name, generation=generation).download_as_text(if_generation_match=generation))
            if datetime.fromisoformat(value['expires']) > now(): return self
        except NotFound: pass
        except PreconditionFailed: return self
        try: self.write(generation)
        except PreconditionFailed: return self
        self.thread = threading.Thread(target=self.renew, daemon=True); self.thread.start(); return self
    def __exit__(self, *args):
        self.stop.set()
        if self.thread: self.thread.join(timeout=2)
        if self.generation is not None:
            try: bucket.blob(ROOT + '/lease.json').delete(if_generation_match=self.generation)
            except (NotFound, PreconditionFailed): pass

def retry_linkedin(company, watch):
    """Recover an existing snapshot first. Only explicit retry may buy a replacement."""
    from core.company import watch_brightdata_service as service
    state = service._load(company, watch)
    if not state or not state.get('snapshot_id'):
        return service.scan_linkedin(company, watch, start=True)  # UNKNOWN remains protected in service.
    if state['status'] != 'FAILED': return service.scan_linkedin(company, watch, start=False)
    provider_status = service.provider.progress(state['snapshot_id'])
    if provider_status in {'failed', 'canceled'}:
        return service.scan_linkedin(company, watch, start=True)
    with service.document_lock('scan-company-' + company):
        latest = service._load(company, watch)
        if latest and latest.get('snapshot_id') == state['snapshot_id'] and latest['status'] == 'FAILED':
            latest.update(status='RUNNING', message=None)
            service._save(company, watch, latest)
    return service.scan_linkedin(company, watch, start=False)

def step_source(source):
    from core.company import watch_discovery_service as discovery
    row = dict(source); c, w = row['id_company'], row['id_company_watch']
    try:
        current = discovery.active_watch(c, w)
        if source_signature(current) != row['signature']:
            return {**row, 'status': 'SKIPPED', 'error': 'Paramètres modifiés pendant la collecte ; lancer un nouveau passage'}
        if row['method'] == 'BRIGHTDATA':
            from core.company import watch_brightdata_service as service
            if row['status'] == 'PENDING' and row['retry']:
                response = retry_linkedin(c, w)
            else:
                response = service.scan_linkedin(c, w, start=row['status'] == 'PENDING' and not row['recover_only'])
        else: response = discovery.scan_watch(c, w)
        monitoring.record(c, w, result=response)
        status = response['status']
        row['warnings'] = response.get('warnings') or []
        if status in {'ok', 'COMPLETE'}:
            row.update(status='COMPLETE', error=None, **{k: response.get(k, 0) for k in ('new', 'known', 'unchanged')})
        elif status in {'STARTING', 'RUNNING'}:
            row.setdefault('started_at', stamp())
            row.update(status='RUNNING', next_poll=(now() + timedelta(seconds=10)).isoformat())
            if now() - datetime.fromisoformat(row['started_at']) > timedelta(minutes=30):
                row.update(status='FAILED', error='Attente fournisseur supérieure à 30 minutes ; le snapshot reste récupérable')
                monitoring.record(c, w, error=row['error'])
        else:
            row.update(status='FAILED', error=response.get('message') or 'Aucune collecte à reprendre' if status == 'IDLE' else response.get('message') or status)
    except Exception as exc:
        excluded = getattr(exc, 'status_code', None) == 404 or (getattr(exc, 'status_code', None) == 409 and any(term in str(getattr(exc, 'detail', '')).lower() for term in ('suspendu', 'inactive')))
        row.update(status='SKIPPED' if excluded else 'FAILED', error=monitoring.safe_message(getattr(exc, 'detail', str(exc))))
        if not excluded: monitoring.record(c, w, error=row['error'])
        log.exception('Watch source failed watch=%s', w)
    return row

def due_sources(pending):
    running = [r for r in pending if r['status'] == 'RUNNING']
    candidates = [r for r in running if not r.get('next_poll') or datetime.fromisoformat(r['next_poll']) <= now()]
    candidates += [r for r in pending if r['status'] == 'PENDING'][:max(0, 3 - len(running))]
    # Existing provider service uses a company-wide lease, not a source lease.
    # Never call two accounts of the same company simultaneously.
    chosen, companies = [], set()
    for source in candidates:
        if source['id_company'] in companies: continue
        chosen.append(source); companies.add(source['id_company'])
        if len(chosen) == 3: break
    return chosen

_drain_lock = threading.Lock()

def drain():
    if not _drain_lock.acquire(blocking=False): return
    try: _drain_queue()
    finally: _drain_lock.release()

def _drain_queue():
    pause = threading.Event()
    try:
        while True:
            jobs = list_jobs()['jobs']
            if not jobs or jobs[0]['status'] != 'RUNNING': return
            with Lease() as lease:
                # After an API restart, wait for the former lease to expire.
                if not lease.valid:
                    pause.wait(3)
                    continue
                while lease.valid:
                    jobs = list_jobs()['jobs']
                    if not jobs or jobs[0]['status'] != 'RUNNING': return
                    job = jobs[0]
                    pending = [r for r in job['sources'] if r['status'] not in TERMINAL]
                    due = due_sources(pending)
                    if pending and not due:
                        pause.wait(1)
                        continue
                    due = due[:3]
                    # Persist dispatch intent BEFORE provider calls. After a crash,
                    # RUNNING rows poll their snapshot; they never repurchase a job.
                    launching = {r['id_company_watch'] for r in due if r['status'] == 'PENDING'}
                    if launching:
                        with lock():
                            dispatch = get_job(job['id_job'])
                            for source in dispatch['sources']:
                                if source['id_company_watch'] in launching:
                                    source.update(status='RUNNING', started_at=stamp())
                            dispatch['updated_at'] = stamp()
                            save(path(job['id_job']), dispatch)
                    with ThreadPoolExecutor(max_workers=3) as pool: updates = list(pool.map(step_source, due))
                    if not lease.valid: return
                    with lock():
                        latest = get_job(job['id_job'])
                        mapped = {r['id_company_watch']: r for r in updates}
                        latest['sources'] = [mapped.get(r['id_company_watch'], r) for r in latest['sources']]
                        latest['updated_at'] = stamp()
                        if all(r['status'] in TERMINAL for r in latest['sources']):
                            latest['status'] = 'PARTIAL' if any(r['status'] != 'COMPLETE' for r in latest['sources']) else 'COMPLETE'
                        save(path(job['id_job']), latest)
                    if latest['status'] != 'RUNNING': return
    except Exception: log.exception('Watch interrupted; persisted progress can be resumed')
