"""Media LinkedIn discovery. Paid launch is async and resumable, no LLM calls."""
from __future__ import annotations
import hashlib
import logging
import json
import os
import uuid
import time
from concurrent.futures import ThreadPoolExecutor
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

def _response(state, *, added_this_call=0, reused_result=False):
    return {'status':state['status'],'snapshot_id':state.get('snapshot_id'),'run_id':state.get('run_id'),
        'discovered_urls':state.get('new',0), 'added_this_call':added_this_call,
        'reused_result':reused_result, 'count_method':state.get('count_method'),
        'received':state.get('received'), 'valid_posts':state.get('valid_posts'),
        'candidates':state.get('candidates'), 'merge_skipped':state.get('merge_skipped'),
        'issue_count':state.get('issue_count'),
        'known':state.get('known',0),'warnings':state.get('warnings',[]),'message':state.get('message'),
        'timings':state.get('timings',{}),'scanned_sources':1,'failed_sources':1 if state['status']=='FAILED' else 0}


def scan(source_id,*,start=False):
    source=get_source(source_id) if start else None
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
        if not state:return {'status':'IDLE','discovered_urls':0,'added_this_call':0,'known':0,'warnings':[]}
        if state['status'] in {'UNKNOWN','STARTING'}:
            return {**_response(state),'status':'UNKNOWN','message':'Lancement incertain : rattacher un snapshot ID depuis Bright Data.'}
        if state['status']!='RUNNING':return _response(state,reused_result=state['status']=='COMPLETE')
        started=time.perf_counter()
        status=provider.progress(state['snapshot_id'])
        logger.info('[MEDIA LINKEDIN] progress source=%s status=%s duration=%.3fs',source_id,status,time.perf_counter()-started)
        if status in {'failed','canceled'}:
            state.update(status='FAILED',message='Collecte fournisseur échouée ou annulée.');_save(source_id,state);return _response(state)
        if status!='ready':return _response(state)
        if state.get('result_uri'):records=json.loads(_read_uri(state['result_uri']))
        else:
            records=provider.download(state['snapshot_id'])
            state['result_uri']=_upload(f"media-linkedin/results/{state['run_id']}.json",json.dumps(records,ensure_ascii=False).encode(),'application/json')
            _save(source_id,state)
        started=time.perf_counter()
        _ingest(source_id,state,records)
        logger.info('[MEDIA LINKEDIN] ingest source=%s posts=%s duration=%.3fs',source_id,len(records),time.perf_counter()-started)
        return _response(state,added_this_call=state.get('new',0))


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
    hashes|={r['CONTENT_HASH'] for r in known if r.get('CONTENT_HASH')}
    ids|={i for r in known if (i:=provider.post_id(r.get('URL')))}
    pending=[];count_known=0
    started=time.perf_counter()
    for post in posts:
        h=content_hash(post['text'])
        if post['post_id'] in ids or h in hashes:count_known+=1;continue
        pending.append({'id':str(uuid.uuid5(uuid.NAMESPACE_URL,BASE+source_id+':'+post['post_id'])),
            'url':post['url'],'title':' '.join(post['text'].split())[:200],
            'published':post['published_at'],'hash':h,'post':post})
        ids.add(post['post_id']);hashes.add(h)
    def upload(item):
        item['capture']=_upload(f"media-linkedin/captures/{state['run_id']}/{item['post']['post_id']}.json",
            json.dumps(item['post'],ensure_ascii=False).encode(),'application/json')
        return {key:value for key,value in item.items() if key!='post'}
    inserted=0
    if pending:
        with ThreadPoolExecutor(max_workers=4) as pool:
            pending=list(pool.map(upload,pending))
        state.setdefault('timings',{})['dedup_and_captures_seconds']=round(time.perf_counter()-started,3)
        started=time.perf_counter()
        # One atomic MERGE for all posts, never a per-URL insert.
        merge_result=query(f"""MERGE `{DISCOVERY}` T USING (
            SELECT JSON_VALUE(p,'$.id') AS ID_DISCOVERY, JSON_VALUE(p,'$.url') AS URL,
              JSON_VALUE(p,'$.title') AS TITLE, JSON_VALUE(p,'$.published') AS PUBLISHED_AT,
              JSON_VALUE(p,'$.capture') AS CAPTURE_URI, JSON_VALUE(p,'$.hash') AS CONTENT_HASH
            FROM UNNEST(JSON_QUERY_ARRAY(PARSE_JSON(@payload))) p
        ) S ON T.ID_DISCOVERY=S.ID_DISCOVERY
        WHEN NOT MATCHED THEN INSERT (ID_DISCOVERY,SOURCE_ID,URL,TITLE,STATUS,DATE_FOUND,CREATED_AT,
            PUBLISHED_AT,CAPTURE_URI,CONTENT_HASH)
        VALUES (S.ID_DISCOVERY,@source,S.URL,S.TITLE,'NEW',CURRENT_TIMESTAMP(),CURRENT_TIMESTAMP(),
            SAFE_CAST(S.PUBLISHED_AT AS TIMESTAMP),S.CAPTURE_URI,S.CONTENT_HASH);
        SELECT @@row_count AS INSERTED_COUNT;""",
            [param('payload','STRING',json.dumps(pending,ensure_ascii=False)),param('source','STRING',source_id)])
        if not merge_result or 'INSERTED_COUNT' not in merge_result[0]:
            raise RuntimeError('Compteur BigQuery INSERTED_COUNT absent ; aucune estimation affichée')
        inserted=int(merge_result[0]['INSERTED_COUNT'])
        if not 0 <= inserted <= len(pending):
            raise RuntimeError('Compteur BigQuery incohérent')
    if pending:state.setdefault('timings',{})['bigquery_merge_seconds']=round(time.perf_counter()-started,3)
    warnings=['La couverture LinkedIn peut être partielle. Le Studio reste disponible pour compléter.']
    if issues:
        _upload(f"media-linkedin/results/{state['run_id']}-issues.json",json.dumps(issues).encode(),'application/json')
        warnings.append(f'{len(issues)} anomalie(s) conservée(s) dans l’audit fournisseur.')
    if len(records)>=state['limit']:warnings.append(f"Plafond de {state['limit']} résultats atteint : collecte potentiellement partielle.")
    state.update(status='COMPLETE' if posts or not records else 'FAILED',new=inserted,known=count_known,warnings=warnings,received=len(records),valid_posts=len(posts),
        candidates=len(pending),merge_skipped=len(pending)-inserted,issue_count=len(issues),count_method='BIGQUERY_ROW_COUNT')
    _save(source_id,state)


def store_discoveries(ids):
    if not ids:return {'status':'ok','stored':0,'skipped':0,'errors':0}
    rows=query(f'SELECT * FROM `{DISCOVERY}` WHERE ID_DISCOVERY IN UNNEST(@ids)',
        [bigquery.ArrayQueryParameter('ids','STRING',ids)])
    grouped={};skipped=0;errors=0;stored=0
    for row in rows:
        if row['STATUS']!='NEW':skipped+=1;continue
        try:
            post=json.loads(_read_uri(row['CAPTURE_URI']))
            if provider.post_id(row['URL'])!=post['post_id']:raise ValueError('Capture incohérente')
            grouped.setdefault(row['SOURCE_ID'],[]).append((row['ID_DISCOVERY'],{
                'raw_text':post['text'],'title':row.get('TITLE'),'source_url':post['url'],'date_source':post['published_at']}))
        except Exception:
            logger.exception("[MEDIA LINKEDIN] Erreur lecture capture discovery=%s",row['ID_DISCOVERY'])
            errors+=1
    for source,items in grouped.items():
        try:
            result=store_posts(source,[post for _,post in items],discovery_ids=[id for id,_ in items])
            stored+=result['stored'];skipped+=result['skipped']
        except Exception:
            logger.exception("[MEDIA LINKEDIN] Erreur stockage RAW source=%s",source)
            errors+=len(items)
    return {'status':'ok','stored':stored,'skipped':skipped,'errors':errors}
