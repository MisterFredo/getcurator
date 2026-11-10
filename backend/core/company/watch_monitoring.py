"""Persistent source diagnostics. Import-safe: services are loaded inside functions only."""
from __future__ import annotations
import functools
import hashlib
import json
import re
from datetime import datetime, timezone
from urllib.parse import urlsplit
from google.api_core.exceptions import NotFound
from config import BQ_PROJECT, BQ_DATASET
from utils.gcs import bucket
from core.library.company_watch_library import document_lock

ROOT = 'company-watch/operations/' + hashlib.sha256(f'{BQ_PROJECT}.{BQ_DATASET}'.encode()).hexdigest()

def stamp(): return datetime.now(timezone.utc).isoformat()
def load(path, default=None):
    try: return json.loads(bucket.blob(ROOT + '/' + path).download_as_text())
    except NotFound: return default

def save(path, value):
    b = bucket.blob(ROOT + '/' + path)
    b.cache_control = 'private, no-store, max-age=0'
    b.upload_from_string(json.dumps(value, ensure_ascii=False, default=str), content_type='application/json')

def key(company, watch):
    return hashlib.sha256(json.dumps([company, watch]).encode()).hexdigest()

def diagnostic_path(company, watch): return 'sources/' + key(company, watch) + '.json'
def linkedin(url):
    host = (urlsplit(url or '').hostname or '').lower()
    return host == 'linkedin.com' or host.endswith('.linkedin.com')

def classify(watch):
    config = watch.get('collection_config') or {}
    if isinstance(config, str): config = json.loads(config)
    channel = 'LINKEDIN' if linkedin(watch.get('source_url')) else 'WEB'
    # Bright Data collects posts, even when an old HTML mode says SINGLE_PAGE.
    single = watch.get('collection_method') != 'BRIGHTDATA' and (
        config.get('mode') == 'SINGLE_PAGE' or (not config.get('mode') and channel == 'LINKEDIN'))
    return channel, 'SINGLE_PAGE' if single else 'PUBLICATIONS'

def safe_message(value):
    text = str(value)[:2000]
    text = re.sub(r'(?i)bearer\s+[^\s\"\']+', 'Bearer [masqué]', text)
    return re.sub(r'(?i)((?:api[_-]?key|token|password|authorization)[\"\']?\s*[:=]\s*)[^\s,;]+', r'\1[masqué]', text)

def record(company, watch, result=None, error=None):
    path = diagnostic_path(company, watch)
    with document_lock('watch-diagnostic-' + key(company, watch)):
        state = load(path, {})
        result = result or {}
        raw = result.get('status', 'FAILED' if error else 'UNKNOWN')
        failed = error is not None or raw in {'FAILED', 'UNKNOWN'}
        complete = raw in {'ok', 'COMPLETE'}
        if raw == 'IDLE': return state  # An empty provider state cannot erase a failure.
        when = stamp()
        state.update(id_company=company, id_company_watch=watch, last_attempt_at=when,
                     status='FAILED' if failed else ('COMPLETE' if complete else 'RUNNING'))
        if failed:
            state['error'] = safe_message(error if error is not None else result.get('message') or raw)
            state['last_failure_at'] = when
        elif complete:
            state['error'] = None
            state['last_success_at'] = when
        # Keep previous problem while a retry is still running.
        state['warnings'] = [safe_message(x) for x in result.get('warnings', state.get('warnings', []))]
        if complete:
            state.update(new=result.get('new', 0), known=result.get('known', 0), unchanged=result.get('unchanged', 0))
        if result.get('snapshot_id'): state['snapshot_id'] = result['snapshot_id']
        save(path, state)
        return state

def tracked_scan(function):
    @functools.wraps(function)
    def wrapped(company_id, watch_id, *args, **kwargs):
        try:
            result = function(company_id, watch_id, *args, **kwargs)
        except Exception as exc:
            # Source exclusion (disabled/deleted) is not a collection failure.
            if getattr(exc, 'status_code', None) not in {404, 409}:
                record(company_id, watch_id, error=getattr(exc, 'detail', str(exc)))
            raise
        record(company_id, watch_id, result=result)
        return result
    return wrapped

def diagnostic(watch):
    value = load(diagnostic_path(watch['id_company'], watch['id_company_watch']))
    if value is not None: return value
    if watch.get('collection_method') != 'BRIGHTDATA': return None
    # Recover diagnostics for existing paid jobs without any provider call.
    from core.company import watch_brightdata_service as provider
    old = provider._load(watch['id_company'], watch['id_company_watch'])
    if not old: return None
    return {'status': 'FAILED' if old.get('status') in {'FAILED', 'UNKNOWN', 'STARTING'} else old.get('status'),
            'last_attempt_at': old.get('updated_at') or old.get('started_at'),
            'last_success_at': old.get('updated_at') if old.get('status') == 'COMPLETE' else None,
            'error': safe_message(old.get('message') or '') or None, 'warnings': old.get('warnings') or [],
            'new': old.get('new', 0), 'known': old.get('known', 0), 'snapshot_id': old.get('snapshot_id'),
            'legacy': True}
