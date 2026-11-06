"""Media LinkedIn discovery. Paid launch is async and resumable, no LLM calls."""
from __future__ import annotations
import hashlib
import logging
import json
import os
import uuid
from datetime import datetime, timezone
from google.cloud import bigquery
from fastapi import HTTPException
from google.api_core.exceptions import NotFound
from utils.gcs import bucket
from core.library.company_watch_library import _upload, _read_uri, document_lock
from core.discovery import brightdata_linkedin as provider
from core.discovery.linkedin_media_store import BASE, content_hash, existing, query, param, store_posts

SOURCE=f'{BASE}.RATECARD_SOURCE'
DISCOVERY=f'{BASE}.RATECARD_SOURCE_DISCOVERY'
logger=logging.getLogger(__name__)


def get_source(source_id):
    rows=query(f'SELECT * FROM `{SOURCE}` WHERE SOURCE_ID=@source LIMIT 1',[param('source','STRING',source_id)])
    if not rows:raise HTTPException(404,'Source introuvable')
    return dict(rows[0])


def _path(source):return 'media-linkedin/jobs/'+hashlib.sha256((BASE+source).encode()).hexdigest()+'.json'
def _load(source):
    try:return json.loads(bucket.blob(_path(source)).download_as_text())
    except NotFound:return None

def _save(source,state):
    bucket.blob(_path(source)).upload_from_string(json.dumps(state,ensure_ascii=False),content_type='application/json')

def _response(state):
    return {'status':state['status'],'snapshot_id':state.get('snapshot_id'),'discovered_urls':state.get('new',0),
        'known':state.get('known',0),'warnings':state.get('warnings',[]),'message':state.get('message'),
        'scanned_sources':1,'failed_sources':1 if state['status']=='FAILED' else 0}


def scan(source_id,*,start=False):
    source=get_source(source_id)
    with document_lock('media-scan-'+hashlib.sha256((BASE+source_id).encode()).hexdigest()):
        state=_load(source_id)
        if start and (not state or state['status'] not in {'RUNNING','STARTING','UNKNOWN'}):
            if source.get('ACQUISITION_MODE')!='LINKEDIN_BRIGHTDATA':raise ValueError('Source non configurée en LinkedIn Bright Data')
            url=source.get('DOMAIN') or ''
            limit=int(os.getenv('MEDIA_LINKEDIN_LIMIT_PER_INPUT','100'))
            config={'limit_per_input':limit};provider.validate_config(url,config)
            provider._token()
            state={'status':'STARTING','url':url,'limit':limit,'run_id':uuid.uuid4().hex}
            _save(source_id,state)
            try:state['snapshot_id']=provider.trigger(url,config)
            except provider.AmbiguousTrigger:
                state.update(status='UNKNOWN',message='Lancement incertain. Rattachez le snapshot ID depuis Bright Data ; aucun nouveau lancement automatique.')
                _save(source_id,state);return _response(state)
            except provider.ProviderError:
                state.update(status='FAILED',message='Échec Bright Data : vérifier le compte et la clé.')
                _save(source_id,state);raise
            state['status']='RUNNING';_save(source_id,state);return _response(state)
        if not state:return {'status':'IDLE','discovered_urls':0,'known':0,'warnings':[]}
        if state['status'] in {'UNKNOWN','STARTING'}:
            return {**_response(state),'status':'UNKNOWN','message':'Lancement incertain : rattacher un snapshot ID depuis Bright Data.'}
        if state['status']!='RUNNING':return _response(state)
        status=provider.progress(state['snapshot_id'])
        if status in {'failed','canceled'}:
            state.update(status='FAILED',message='Collecte fournisseur échouée ou annulée.');_save(source_id,state);return _response(state)
        if status!='ready':return _response(state)
        if state.get('result_uri'):records=json.loads(_read_uri(state['result_uri']))
        else:
            records=provider.download(state['snapshot_id'])
            state['result_uri']=_upload(f"media-linkedin/results/{state['run_id']}.json",json.dumps(records,ensure_ascii=False).encode(),'application/json')
            _save(source_id,state)
        _ingest(source_id,state,records)
        return _response(state)


def attach(source_id,snapshot_id):
    get_source(source_id);snapshot_id=provider._snapshot(snapshot_id)
    with document_lock('media-scan-'+hashlib.sha256((BASE+source_id).encode()).hexdigest()):
        state=_load(source_id)
        if not state or state['status'] not in {'UNKNOWN','STARTING'}:raise HTTPException(409,'Aucun lancement incertain à rattacher')
        provider.progress(snapshot_id)
        state.update(snapshot_id=snapshot_id,status='RUNNING',message=None);_save(source_id,state)
        return _response(state)


def _ingest(source_id,state,records):
    expected=provider.account_url(state['url'])[0]
    for record in records:
        origin=(record.get('discovery_input') or {}).get('url') if isinstance(record,dict) else None
        if not origin or provider.account_url(origin)[0]!=expected:raise ValueError('La collecte ne correspond pas au compte suivi')
    posts,issues=provider.normalize_records(records)
    hashes,ids=existing(source_id)
    known=query(f'SELECT URL, CONTENT_HASH FROM `{DISCOVERY}` WHERE SOURCE_ID=@source',[param('source','STRING',source_id)])
