"""Member CONNECTIONS only. Durable preview, company-first matching, insert-only import."""
from __future__ import annotations
import hashlib
import json
import logging
import os
import re
import time
import unicodedata
import uuid
from datetime import datetime, timezone
from difflib import SequenceMatcher
from urllib.parse import urlsplit, parse_qs
import requests
from fastapi import HTTPException
from google.cloud import bigquery
from google.api_core.exceptions import NotFound,PreconditionFailed
from api.contact.models import ContactCreate, linkedin_profile
from core.contact import service as contacts

log = logging.getLogger(__name__)
IMPLEMENTATION_VERSION = 'contacts-linkedin-1.3-bq'
BASE = contacts.BASE
MAP = f'{BASE}.RATECARD_CONTACT_LINKEDIN_COMPANY_MAP'
ENDPOINT = 'https://api.linkedin.com/rest/memberSnapshotData'
PREFIX = 'contact-imports/v1/' + hashlib.sha256(BASE.encode()).hexdigest()[:20]
MAX_ROWS, MAX_PAGES, MAX_SECONDS = 30000, 500, 600

def now(): return datetime.now(timezone.utc).isoformat()
def normalized(value):
    return ' '.join(unicodedata.normalize('NFKC', str(value or '')).casefold().split())
def group_key(value): return hashlib.sha256(normalized(value).encode()).hexdigest()
def row_key(url): return hashlib.sha256(url.encode()).hexdigest()
def blob(name):
    from utils.gcs import bucket
    return bucket.blob(f'{PREFIX}/{name}.json')
def lock(name):
    from core.library.company_watch_library import document_lock
    return document_lock('contact-import-'+hashlib.sha256((BASE+name).encode()).hexdigest())
def read_blob(name):
    # Public/default object URLs can retain an older response in intermediary caches.
    # Pin every download to the current GCS generation obtained from metadata.
    for _ in range(3):
        b=blob(name)
        try:
            b.reload()
            return json.loads(b.download_as_text(if_generation_match=b.generation))
        except (NotFound,PreconditionFailed):
            continue
    raise HTTPException(404,'Aperçu introuvable ou modifié pendant la lecture ; réessayer')

def read(run_id):
    if not re.fullmatch(r'[0-9a-f-]{36}',run_id): raise HTTPException(400,'Identifiant de collecte invalide')
    return read_blob(run_id)

def save(run):
    run['updated_at']=now()
    b=blob(run['id_run'])
    b.cache_control='no-store'
    b.upload_from_string(json.dumps(run,ensure_ascii=False),content_type='application/json')
def fresh(run):
    return time.time()-datetime.fromisoformat(run['updated_at']).timestamp()<180

def start():
    if not os.environ.get('LINKEDIN_ACCESS_TOKEN','').strip(): raise HTTPException(400,'LINKEDIN_ACCESS_TOKEN absent du backend')
    with lock('start'):
        latest=blob('latest')
        if latest.exists():
            old=read(read_blob('latest')['id_run'])
            if old['status'] in ('FETCHING','IMPORTING') and fresh(old): return {'id_run':old['id_run'],'queued':False}
        run={'id_run':str(uuid.uuid4()),'status':'FETCHING','created_at':now(),'updated_at':now(),
             'rows':[],'pages':0,'next_start':0,'fingerprints':[],'error':None,'result':None}
        save(run)
        latest.cache_control='no-store'
        latest.upload_from_string(json.dumps({'id_run':run['id_run']}),content_type='application/json')
        return {'id_run':run['id_run'],'queued':True}

def page(response, start_value):
    # Never return response bodies/headers or token-bearing exceptions to the UI/logs.
    try: data=response.json()
    except ValueError: raise ValueError('LINKEDIN_INVALID_JSON')
    message=str(data.get('message','')) if isinstance(data,dict) else ''
    terminal_message=' '.join(message.casefold().strip().rstrip('.').split())
    if response.status_code in (400,404) and terminal_message in {
        'no data found for this memberid',
        'no data found for this member',
        'no data found for this domain and memberid',
    }: return None,None
    if response.status_code!=200: raise ValueError(f'LINKEDIN_HTTP_{response.status_code}')
    if not isinstance(data,dict): raise ValueError('LINKEDIN_INVALID_SHAPE')
    elements=data.get('elements')
    if isinstance(elements,dict): elements=[elements]
    if not isinstance(elements,list) or not elements: raise ValueError('LINKEDIN_DATA_NOT_READY')
    rows=[]
    for element in elements:
        if not isinstance(element,dict) or element.get('snapshotDomain')!='CONNECTIONS': raise ValueError('LINKEDIN_UNEXPECTED_DOMAIN')
        values=element.get('snapshotData')
        if not isinstance(values,list) or any(not isinstance(v,dict) for v in values): raise ValueError('LINKEDIN_INVALID_ROWS')
        rows.extend(values)
    if not rows: raise ValueError('LINKEDIN_DATA_NOT_READY')
    # total is not a reliable terminal marker. Follow next, otherwise probe next page.
    next_start=start_value+1
    paging=data.get('paging') or {}
    for item in paging.get('links',[]):
        if item.get('rel')=='next':
            parts=urlsplit(str(item.get('href','')))
            if parts.scheme and (parts.scheme!='https' or parts.netloc!='api.linkedin.com'): raise ValueError('LINKEDIN_INVALID_PAGINATION')
            if parts.path!='/rest/memberSnapshotData': raise ValueError('LINKEDIN_INVALID_PAGINATION')
            params=parse_qs(parts.query)
            if params.get('domain',['CONNECTIONS'])!=['CONNECTIONS']: raise ValueError('LINKEDIN_INVALID_PAGINATION')
            try: next_start=int(params['start'][0])
            except (ValueError,KeyError,IndexError): raise ValueError('LINKEDIN_INVALID_PAGINATION')
            if next_start<=start_value: raise ValueError('LINKEDIN_PAGINATION_LOOP')
    return rows,next_start

def collect(run_id):
    with lock(run_id):
        run=read(run_id)
        if run['status']!='FETCHING': return
        began=time.monotonic()
        try:
            token=os.environ.get('LINKEDIN_ACCESS_TOKEN','').strip()
            if not token: raise ValueError('LINKEDIN_TOKEN_MISSING')
            with requests.Session() as session:
                while True:
                    if time.monotonic()-began>MAX_SECONDS: raise ValueError('LINKEDIN_TIME_BUDGET')
                    if run['pages']>=MAX_PAGES or len(run['rows'])>=MAX_ROWS: raise ValueError('LINKEDIN_SAFETY_LIMIT')
                    response=session.get(ENDPOINT,params={'q':'criteria','domain':'CONNECTIONS','start':run['next_start']},
                       headers={'Authorization':f'Bearer {token}','Linkedin-Version':'202312','Accept':'application/json'},
                       timeout=(10,60),allow_redirects=False)
                    rows,next_start=page(response,run['next_start'])
                    if rows is None:
                        if not run['pages']: raise ValueError('LINKEDIN_DATA_NOT_READY')
                        run['status']='READY';run['error']=None;save(run);return
                    digest=hashlib.sha256(json.dumps(rows,sort_keys=True,ensure_ascii=False).encode()).hexdigest()
                    if digest in run['fingerprints']: raise ValueError('LINKEDIN_REPEATED_PAGE')
                    if len(run['rows'])+len(rows)>MAX_ROWS: raise ValueError('LINKEDIN_SAFETY_LIMIT')
                    run['rows'].extend(rows);run['fingerprints'].append(digest);run['pages']+=1;run['next_start']=next_start
                    save(run)
        except Exception as exc:
            code=str(exc) if isinstance(exc,ValueError) and str(exc).startswith('LINKEDIN_') else 'LINKEDIN_REQUEST_FAILED'
            run['status']='PARTIAL' if run['pages'] else 'FAILED';run['error']=code;save(run)
            log.warning('Contact LinkedIn import %s: %s',run_id,code)

def resume(run_id):
    with lock(run_id):
        run=read(run_id)
        if run['status'] in ('FETCHING','IMPORTING') and fresh(run): return {'id_run':run_id,'queued':False}
        if run['status'] in ('READY','IMPORTED'): raise HTTPException(409,'Collecte déjà terminée')
        phase='IMPORT' if run.get('prepared') else 'FETCH'
        run['status']='IMPORTING' if phase=='IMPORT' else 'FETCHING';run['error']=None;save(run)
        return {'id_run':run_id,'queued':True,'phase':phase}

def directory():
    companies=[dict(r) for r in contacts.query(f"SELECT ID_COMPANY,NAME FROM `{contacts.COMPANY}` WHERE IS_ACTIVE=TRUE")]
    aliases=[dict(r) for r in contacts.query(f'SELECT ID_COMPANY,ALIAS FROM `{BASE}.RATECARD_COMPANY_ALIAS`')]
    remembered=[dict(r) for r in contacts.query(f'SELECT COMPANY_KEY,ID_COMPANY FROM `{MAP}`')]
    return companies,aliases,remembered

def matching(companies,aliases,remembered):
    names={r['ID_COMPANY']:r['NAME'] for r in companies};index={}
    for r in companies+ [{'ID_COMPANY':a['ID_COMPANY'],'NAME':a['ALIAS']} for a in aliases]:
        key=normalized(r['NAME'])
        if key and r['ID_COMPANY'] in names:index.setdefault(key,set()).add(r['ID_COMPANY'])
    memory={}
    for r in remembered:
        if r['ID_COMPANY'] in names:memory.setdefault(r['COMPANY_KEY'],set()).add(r['ID_COMPANY'])
    return names,index,memory

def candidates(raw_rows):
    valid={};invalid=0;duplicates=0;conflicts=set()
    for raw in raw_rows:
        try:
            profile=linkedin_profile(raw.get('URL'))
            if not profile: raise ValueError('missing URL')
            values={'first_name':str(raw.get('First Name') or '').strip(),'last_name':str(raw.get('Last Name') or '').strip(),
                    'linkedin_url':profile,'job_title':str(raw.get('Position') or '').strip() or None,
                    'email':str(raw.get('Email Address') or '').strip() or None}
            # An invalid optional email must not lose an otherwise usable relation.
            email_warning=False
            try: parsed=ContactCreate(**values)
            except ValueError:
                if values['email']:
                    values['email']=None;email_warning=True;parsed=ContactCreate(**values)
                else:raise
            item=parsed.dict();item.update({'key':row_key(profile),'company_label':str(raw.get('Company') or '').strip(),
              'connected_on':str(raw.get('Connected On') or ''),'email_warning':email_warning})
            item['group_key']=group_key(item['company_label'])
            if profile in valid:
                duplicates+=1
                if valid[profile]['group_key']!=item['group_key']: conflicts.add(profile)
            else:valid[profile]=item
        except (ValueError,TypeError):invalid+=1
    for profile in conflicts:valid.pop(profile,None)
    return list(valid.values()),{'invalid':invalid,'duplicates':duplicates,'conflicting_profiles':len(conflicts)}

def preview(run_id):
    run=read(run_id)
    status=run['status']
    if status in ('FETCHING','IMPORTING') and not fresh(run):status='INTERRUPTED'
    result={k:run.get(k) for k in ['id_run','pages','error','result','created_at']}
    result.update(implementation_version=IMPLEMENTATION_VERSION,status=status,received=len(run['rows']),phase='IMPORT' if run.get('prepared') else 'FETCH',import_processed=run.get('import_processed',0),import_total=len(run.get('prepared',[])))
    if status not in ('READY','IMPORTED'):return result
    companies,aliases,remembered=directory();names,index,memory=matching(companies,aliases,remembered)
    rows,stats=candidates(run['rows']);existing=contacts.query(f'SELECT LINKEDIN_URL,EMAIL FROM `{contacts.CONTACT}`')
    urls=set();emails=set()
    for r in existing:
        try:urls.add(linkedin_profile(r.get('LINKEDIN_URL')))
        except ValueError:pass
        if r.get('EMAIL'):emails.add(normalized(r['EMAIL']))
    groups={};suggestion_cache={};suggestion_index={}
    for name in index:
        tokens={t for t in re.findall(r'\w+',name) if len(t)>=3 and t not in {'the','group','groupe','company'}}
        for token in tokens|{name[:3]}:suggestion_index.setdefault(token,set()).add(name)
    for row in rows:
        key=row['group_key'];label=row['company_label'];matches=(memory.get(key) or index.get(normalized(label),set())) if normalized(label) else set()
        options=sorted(matches)
        g=groups.setdefault(key,{'key':key,'label':label or '(Société non renseignée)',
          'company_id':options[0] if len(options)==1 else '',
          'match':'MATCHED' if len(options)==1 else 'AMBIGUOUS' if options else 'UNMATCHED',
          'suggestions':[{'id_company':i,'name':names[i]} for i in options], 'contacts':[]})
        if not options and label and not g['suggestions']:
            needle=normalized(label)
            if key not in suggestion_cache:
                tokens={t for t in re.findall(r'\w+',needle) if len(t)>=3 and t not in {'the','group','groupe','company'}}|{needle[:3]}
                pool=set().union(*(suggestion_index.get(t,set()) for t in tokens))
                suggestion_cache[key]=sorted(((SequenceMatcher(None,needle,n).ratio(),i) for n in sorted(pool)[:100] for i in index[n]),reverse=True)
            scores=suggestion_cache[key]
            seen=set()
            for score,i in scores:
                if score<0.65 or len(g['suggestions'])>=3:break
                if i not in seen:g['suggestions'].append({'id_company':i,'name':names[i]});seen.add(i)
        row['existing']=row['linkedin_url'] in urls or bool(row['email'] and normalized(row['email']) in emails)
        g['contacts'].append(row)
    result.update(groups=sorted(groups.values(),key=lambda g:(g['match']!='MATCHED',normalized(g['label']))),stats=stats,
      companies=[{'id_company':i,'name':name} for i,name in sorted(names.items(),key=lambda x:x[1])])
    return result

def commit(run_id, selections):
    with lock(run_id):
        run=read(run_id)
        if run['status']=='IMPORTED':return {'id_run':run_id,'status':'IMPORTED','queued':False}
        if run['status']=='IMPORTING':return {'id_run':run_id,'status':'IMPORTING','queued':False}
        if run['status']!='READY':raise HTTPException(409,'Terminer la récupération de toutes les pages avant import')
        rows,stats=candidates(run['rows']);by_key={r['key']:r for r in rows}
        companies,aliases,remembered=directory();names,_,_=matching(companies,aliases,remembered)
        chosen={};maps={};prepared=[]
        for selection in selections:
            key=selection.group_key;company=selection.id_company
            if key in maps:raise HTTPException(400,'Société LinkedIn sélectionnée plusieurs fois')
            if company not in names:raise HTTPException(409,'Société GetCurator absente ou inactive ; actualiser')
            maps[key]=company
            if not selection.contact_keys:raise HTTPException(400,'Sélection de contacts vide')
            for contact_key in selection.contact_keys:
                row=by_key.get(contact_key)
                if not row or row['group_key']!=key or contact_key in chosen:raise HTTPException(400,'Sélection de contacts invalide')
                chosen[contact_key]=row
                payload=ContactCreate(**{k:row[k] for k in ['first_name','last_name','email','linkedin_url','job_title']},id_company=company)
                record=payload.dict();record.update(id_contact=str(uuid.uuid5(uuid.NAMESPACE_URL,BASE+'|linkedin|'+row['linkedin_url'])),
                  id_affiliation=str(uuid.uuid4()),company_key=key,company_label=row['company_label'],connected_on=row['connected_on'])
                prepared.append(record)
        if not prepared:raise HTTPException(400,'Sélectionner au moins un contact')
        # Same email across new profiles: preserve only one address, never merge people by name.
        seen_emails=set();email_conflicts=0
        for row in prepared:
            email=row['email']
            if email and email in seen_emails:row['email']=None;email_conflicts+=1
            elif email:seen_emails.add(email)
        run.update(status='IMPORTING',prepared=prepared,import_processed=0,error=None,
          result={'imported':0,'skipped':0,'email_conflicts':email_conflicts})
        save(run)
        return {'id_run':run_id,'status':'IMPORTING','queued':True}

def write_batch(run_id,prepared):
    params=[contacts.p('rows','STRING',json.dumps(prepared,ensure_ascii=False)),contacts.p('run','STRING',run_id)]
    output=contacts.query(f"""CREATE TEMP TABLE incoming AS
          SELECT JSON_VALUE(j,'$.id_contact') ID_CONTACT,JSON_VALUE(j,'$.id_affiliation') ID_AFFILIATION,
            JSON_VALUE(j,'$.first_name') FIRST_NAME,JSON_VALUE(j,'$.last_name') LAST_NAME,
            JSON_VALUE(j,'$.email') EMAIL,JSON_VALUE(j,'$.linkedin_url') LINKEDIN_URL,
            JSON_VALUE(j,'$.job_title') JOB_TITLE,JSON_VALUE(j,'$.id_company') ID_COMPANY,
            JSON_VALUE(j,'$.company_key') COMPANY_KEY,JSON_VALUE(j,'$.company_label') COMPANY_LABEL,
            JSON_VALUE(j,'$.connected_on') CONNECTED_ON
          FROM UNNEST(JSON_QUERY_ARRAY(PARSE_JSON(@rows))) j;
          BEGIN TRANSACTION;
          CREATE TEMP TABLE new_contacts AS
            SELECT i.* FROM incoming i
            WHERE NOT EXISTS (
              SELECT 1 FROM `{contacts.CONTACT}` c
              WHERE c.ID_CONTACT=i.ID_CONTACT
            )
            AND NOT EXISTS (
              SELECT 1 FROM `{contacts.CONTACT}` c
              WHERE LOWER(RTRIM(c.LINKEDIN_URL,'/'))=LOWER(RTRIM(i.LINKEDIN_URL,'/'))
            )
            AND NOT EXISTS (
              SELECT 1 FROM `{contacts.CONTACT}` c
              WHERE LOWER(c.EMAIL)=i.EMAIL
            );
          INSERT INTO `{contacts.CONTACT}`(ID_CONTACT,FIRST_NAME,LAST_NAME,EMAIL,LINKEDIN_URL,JOB_TITLE,IS_ACTIVE,CREATED_AT,UPDATED_AT,
            IMPORT_SOURCE,IMPORT_RUN_ID,LINKEDIN_COMPANY_LABEL,LINKEDIN_CONNECTED_ON)
            SELECT ID_CONTACT,FIRST_NAME,LAST_NAME,EMAIL,LINKEDIN_URL,JOB_TITLE,TRUE,CURRENT_TIMESTAMP(),CURRENT_TIMESTAMP(),
              'LINKEDIN_CONNECTIONS',@run,COMPANY_LABEL,SAFE.PARSE_DATE('%d %b %Y',CONNECTED_ON) FROM new_contacts;
          INSERT INTO `{contacts.AFFILIATION}`(ID_CONTACT_COMPANY,ID_CONTACT,ID_COMPANY,JOB_TITLE,STARTED_AT,ENDED_AT,CREATED_AT,UPDATED_AT)
            SELECT ID_AFFILIATION,ID_CONTACT,ID_COMPANY,JOB_TITLE,CURRENT_TIMESTAMP(),NULL,CURRENT_TIMESTAMP(),CURRENT_TIMESTAMP() FROM new_contacts;
          MERGE `{MAP}` T USING(SELECT COMPANY_KEY,ANY_VALUE(COMPANY_LABEL) AS COMPANY_LABEL,ANY_VALUE(ID_COMPANY) AS ID_COMPANY FROM incoming WHERE TRIM(COMPANY_LABEL)!='' GROUP BY COMPANY_KEY) S ON T.COMPANY_KEY=S.COMPANY_KEY
            WHEN MATCHED THEN UPDATE SET ID_COMPANY=S.ID_COMPANY,LINKEDIN_LABEL=S.COMPANY_LABEL,UPDATED_AT=CURRENT_TIMESTAMP()
            WHEN NOT MATCHED THEN INSERT(COMPANY_KEY,LINKEDIN_LABEL,ID_COMPANY,CREATED_AT,UPDATED_AT)
              VALUES(S.COMPANY_KEY,S.COMPANY_LABEL,S.ID_COMPANY,CURRENT_TIMESTAMP(),CURRENT_TIMESTAMP());
          COMMIT TRANSACTION;
          SELECT (SELECT COUNT(*) FROM `{contacts.CONTACT}` WHERE IMPORT_RUN_ID=@run AND ID_CONTACT IN (SELECT ID_CONTACT FROM incoming)) AS IMPORTED,(SELECT COUNT(*) FROM incoming)-(SELECT COUNT(*) FROM `{contacts.CONTACT}` WHERE IMPORT_RUN_ID=@run AND ID_CONTACT IN (SELECT ID_CONTACT FROM incoming)) AS SKIPPED;""",params)
    return {'imported':int(output[0]['IMPORTED']),'skipped':int(output[0]['SKIPPED'])}

def import_selected(run_id):
    with lock(run_id):
        run=read(run_id)
        if run['status']!='IMPORTING':return
        began=time.monotonic()
        try:
            while run['import_processed']<len(run['prepared']):
                if time.monotonic()-began>MAX_SECONDS:raise ValueError('IMPORT_TIME_BUDGET')
                batch=run['prepared'][run['import_processed']:run['import_processed']+500]
                # Recheck the company immediately before each write; never create companies.
                with contacts.scope_lock():
                    ids={r['id_company'] for r in batch}
                    params=[bigquery.ArrayQueryParameter('ids','STRING',sorted(ids))]
                    valid={r['ID_COMPANY'] for r in contacts.query(f'SELECT ID_COMPANY FROM `{contacts.COMPANY}` WHERE ID_COMPANY IN UNNEST(@ids) AND IS_ACTIVE=TRUE',params)}
                    if valid!=ids:raise ValueError('IMPORT_COMPANY_CHANGED')
                    result=write_batch(run_id,batch)
                run['result']['imported']+=result['imported'];run['result']['skipped']+=result['skipped']
                run['import_processed']+=len(batch);save(run)
            run['status']='IMPORTED';run['error']=None;save(run)
        except Exception as exc:
            code=str(exc) if isinstance(exc,ValueError) and str(exc).startswith('IMPORT_') else 'IMPORT_WRITE_FAILED'
            run['status']='PARTIAL';run['error']=code;save(run)
            log.exception('Contact import %s: %s',run_id,code)
