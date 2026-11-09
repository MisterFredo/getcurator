"""Manual, resumable employer controls. No recurrence or age threshold."""
import json
import logging
import os
import time
import uuid
from datetime import datetime,timezone
from fastapi import HTTPException
from api.contact.models import linkedin_profile
from core.contact import service as contacts
from core.contact import linkedin_import as storage
from core.contact import employer_matching as matching
from core.contact import employer_store as db
from core.discovery import brightdata_linkedin as provider

log=logging.getLogger(__name__)
BATCH_SIZE=50
WORK_SECONDS=240
KIND='EMPLOYER_CHECK'

def iso(value):
    if isinstance(value,datetime):return value.replace(tzinfo=value.tzinfo or timezone.utc).isoformat()
    return value

def read(run_id):
    run=storage.read(run_id)
    if run.get('kind')!=KIND:raise HTTPException(404,'Contrôle employeurs introuvable')
    return run

def latest():
    b=storage.blob('employer-latest')
    return read(storage.read_blob('employer-latest')['id_run']) if b.exists() else None

def save_latest(run):
    storage.save(run);b=storage.blob('employer-latest');b.cache_control='no-store'
    b.upload_from_string(json.dumps({'id_run':run['id_run']}),content_type='application/json')

def status(run_id=None):
    run=read(run_id) if run_id else latest()
    if not run:return {'job':None}
    counts={}
    for item in run['items']:counts[item['status']]=counts.get(item['status'],0)+1
    return {'job':{k:run.get(k) for k in ['id_run','status','created_at','updated_at','excluded_network','network_snapshot_at','include_network','error','snapshots','mode']},
            'counts':counts,'total':len(run['items']),'items':[{k:v for k,v in item.items() if k not in ('raw','decision')} for item in run['items']]}

def selected(include_network):
    # Include automatically suspended unresolved contacts; ordinary manual suspension
    # changes UPDATED_AT, so it is respected and not silently reactivated.
    rows=contacts.query(f'''WITH current_contacts AS ({contacts.READ})
      SELECT c.* FROM current_contacts c LEFT JOIN `{db.TABLE}` e ON e.ID_CONTACT=c.ID_CONTACT
      WHERE c.IS_ACTIVE=TRUE AND c.LINKEDIN_URL IS NOT NULL AND
        (c.LINKEDIN_FOLLOW_ENABLED=TRUE OR
          (e.STATUS IN ('UNMATCHED','REVIEW') AND e.CONTACT_UPDATED_AT=c.UPDATED_AT))
      ORDER BY c.ID_CONTACT LIMIT 10001''')
    if len(rows)>10000:raise HTTPException(400,'Plus de 10 000 contacts : réduire le périmètre avant lancement')
    skip=0;items=[]
    for row in rows:
        person=contacts.out(row)
        if not include_network and person.get('network_status')=='CONFIRMED':skip+=1;continue
        try:url=linkedin_profile(person['linkedin_url'])
        except ValueError:continue
        items.append({'id_contact':person['id_contact'],'name':person['display_name'],'first_name':person['first_name'],
            'last_name':person['last_name'],'profile_url':url,'old_company':person.get('id_company'),
            'old_company_name':person.get('company_name'),'expected_updated_at':iso(person['updated_at']),
            'status':'PENDING','op_token':str(uuid.uuid4())})
    snapshot=contacts.query(f"SELECT COLLECTED_AT FROM `{contacts.NETWORK_STATE}` WHERE NETWORK_KEY='PRIMARY' LIMIT 1")
    return items,skip,iso(snapshot[0]['COLLECTED_AT']) if snapshot else None

def start(include_network=False):
    provider._token()  # Validate before reserving a paid batch.
    with storage.lock('employer-start'):
        old=latest()
        if old and old['status'] in ('RUNNING','PARTIAL','NEEDS_SNAPSHOT'):
            return {'id_run':old['id_run'],'queued':False,'reused':True}
        items,skip,snapshot=selected(include_network)
        run={'id_run':str(uuid.uuid4()),'kind':KIND,'mode':'PROFILES','status':'RUNNING' if items else 'COMPLETE',
             'created_at':storage.now(),'include_network':include_network,'excluded_network':skip,'network_snapshot_at':snapshot,
             'items':items,'snapshots':[],'error':None,'batch':None}
        save_latest(run)
        return {'id_run':run['id_run'],'queued':bool(items),'reused':False}

def directory():
    companies=[dict(r) for r in contacts.query(f'SELECT ID_COMPANY,NAME,LINKEDIN_URL,IS_ACTIVE FROM `{contacts.COMPANY}`')]
    aliases=[dict(r) for r in contacts.query(f'SELECT ID_COMPANY,ALIAS FROM `{contacts.BASE}.RATECARD_COMPANY_ALIAS`')]
    memory=[dict(r) for r in contacts.query(f'SELECT COMPANY_KEY,ID_COMPANY FROM `{storage.MAP}`')]
    return companies,aliases,memory

def decide(item,profile,companies,aliases,memory):
    data={k:item.get(k) for k in ['id_contact','profile_url','old_company','expected_updated_at','op_token','expected_check_run']}
    data.update(status='ERROR',target_company=None,source_name=None,source_url=None,reason='Profil absent de la réponse Bright Data')
    if profile is None:return data
    if profile.get('error') or profile.get('error_code'):data['reason']='Erreur Bright Data sur ce profil';return data
    try:returned=linkedin_profile(profile.get('url'))
    except ValueError:returned=None
    if returned!=item['profile_url']:
        data.update(status='REVIEW',reason='Profil absent ou redirigé : vérifier son identité');return data
    observed,error=matching.employer(profile)
    if not observed:
        data.update(status='REVIEW',reason=error);return data
    data.update(source_name=observed['name'],source_url=observed['url'])
    target,reason=matching.match(observed,companies,aliases,memory,storage.normalized,storage.group_key)
    data.update(target_company=target,reason=reason or 'Employeur déclaré rapproché sans ambiguïté')
    if target:data['status']='CONFIRMED' if target==item.get('old_company') else 'MOVED'
    elif reason=='Société à rapprocher':data['status']='UNMATCHED'
    else:data['status']='REVIEW'
    return data

def result_map(rows,items):
    expected={i['profile_url'] for i in items};found={};duplicates=set()
    for row in rows:
        if not isinstance(row,dict):continue
        raw_input=row.get('input') or {}
        source=row.get('input_url') or (raw_input.get('url') if isinstance(raw_input,dict) else None) or row.get('url')
        try:url=linkedin_profile(source)
        except ValueError:continue
        if url not in expected:continue
        if url in found:duplicates.add(url)
        else:found[url]=row
    for url in duplicates:found[url]={'error':'duplicate_records'}
    return found

def write_decisions(run,items,decisions):
    # Save operation tokens/decisions before BQ. A replay sees OP_TOKEN and never
    # closes a second affiliation or overwrites an already successful result.
    for item,decision in zip(items,decisions):item['decision']=decision
    storage.save(run)
    with contacts.scope_lock():saved=db.write(run['id_run'],decisions)
    by_id={r['ID_CONTACT']:r for r in saved}
    for item in items:
        row=by_id.get(item['id_contact'])
        if not row or row.get('OP_TOKEN')!=item['op_token']:
            item.update(status='CONFLICT',reason='Un autre contrôle a modifié cette fiche');continue
        item.update(status=row.get('LAST_ATTEMPT_STATUS') or row['STATUS'],reason=row.get('REASON'),
          source_name=row.get('SOURCE_COMPANY_NAME'),source_url=row.get('SOURCE_COMPANY_URL'),target_company=row.get('MATCHED_ID_COMPANY'))
        item.pop('decision',None)
    storage.save(run)

def _collect_slice(run_id):
    with storage.lock('employer-worker'),storage.lock(run_id):
        run=read(run_id)
        if run['status']!='RUNNING':return
        began=time.monotonic()
        try:
            if run.get('mode')=='MAPPINGS':
                pending_items=[i for i in run['items'] if i['status']=='PENDING']
                for offset in range(0,len(pending_items),BATCH_SIZE):
                    if time.monotonic()-began>WORK_SECONDS:
                        storage.save(run);return True
                    batch=pending_items[offset:offset+BATCH_SIZE]
                    write_decisions(run,batch,[i['decision'] for i in batch])
                run['status']='COMPLETE';storage.save(run);return
            companies,aliases,memory=directory()
            while any(i['status']=='PENDING' for i in run['items']):
                if time.monotonic()-began>WORK_SECONDS:
                    storage.save(run);return True
                if not run.get('batch'):
                    ids=[i['id_contact'] for i in run['items'] if i['status']=='PENDING'][:BATCH_SIZE]
                    run['batch']={'ids':ids,'stage':'TRIGGERING','snapshot_id':None};storage.save(run)
                    try:
                        batch=[i for i in run['items'] if i['id_contact'] in ids]
                        value=provider._request('POST','/trigger',params={'dataset_id':os.environ.get('BRIGHTDATA_LINKEDIN_PROFILE_DATASET','gd_l1viktl72bvl7bjuj0'),'format':'json','include_errors':'true'},json=[{'url':i['profile_url']} for i in batch])
                        snap=provider._snapshot(value['snapshot_id'])
                    except Exception:
                        run.update(status='NEEDS_SNAPSHOT',error='Lancement sans identifiant confirmé. Vérifier Bright Data avant toute nouvelle collecte ; rattacher le snapshot si disponible.');storage.save(run);return
                    run['batch'].update(stage='WAITING',snapshot_id=snap);run['snapshots'].append(snap);storage.save(run)
                batch_state=run['batch']
                if not batch_state.get('snapshot_id'):
                    run.update(status='NEEDS_SNAPSHOT',error='Un lancement a pu être accepté. Rattacher son snapshot ; aucun nouvel appel payant envoyé.');storage.save(run);return
                progress=provider.progress(batch_state['snapshot_id'])
                if progress in ('starting','running'):
                    time.sleep(3);continue
                batch=[i for i in run['items'] if i['id_contact'] in batch_state['ids']]
                if progress in ('failed','canceled'):
                    found={}
                else:found=result_map(provider.download(batch_state['snapshot_id']),batch)
                decisions=[i.get('decision') or decide(i,found.get(i['profile_url']),companies,aliases,memory) for i in batch]
                write_decisions(run,batch,decisions)
                run['batch']=None;storage.save(run)
            run.update(status='COMPLETE',error=None);storage.save(run)
        except Exception:
            log.exception('Employer control interrupted run=%s',run_id)
            run.update(status='PARTIAL',error='Traitement interrompu ; les résultats acquis sont conservés. Reprendre le même contrôle.');storage.save(run)

def collect(run_id):
    # Renew existing 15-minute document leases between short slices, without
    # requiring the browser or manually resuming a normal long-running job.
    while True:
        try:continuing=_collect_slice(run_id)
        except HTTPException as exc:
            if exc.status_code==409:return  # Another worker already owns this job.
            raise
        if not continuing:return


def resume(run_id,snapshot_id=None):
    with storage.lock(run_id):
        run=read(run_id)
        if run['status']=='COMPLETE':return {'id_run':run_id,'queued':False}
        if snapshot_id:
            if not run.get('batch'):raise HTTPException(409,'Aucun lot à rattacher')
            snap=provider._snapshot(snapshot_id);provider.progress(snap)
            if run['batch'].get('snapshot_id') and run['batch']['snapshot_id']!=snap:raise HTTPException(409,'Ce lot possède déjà un snapshot')
            run['batch'].update(snapshot_id=snap,stage='WAITING')
            if snap not in run['snapshots']:run['snapshots'].append(snap)
        if run['status']=='NEEDS_SNAPSHOT' and not snapshot_id:raise HTTPException(409,'Rattacher le snapshot Bright Data avant de reprendre')
        run.update(status='RUNNING',error=None);storage.save(run)
        return {'id_run':run_id,'queued':True}

def pending():
    rows=contacts.query(f'''WITH current_contacts AS ({contacts.READ})
      SELECT e.*,c.FIRST_NAME,c.LAST_NAME,c.COMPANY_NAME,c.ID_COMPANY,c.UPDATED_AT AS CURRENT_UPDATED_AT
      FROM `{db.TABLE}` e JOIN current_contacts c ON c.ID_CONTACT=e.ID_CONTACT
      WHERE e.STATUS IN ('UNMATCHED','REVIEW') AND c.IS_ACTIVE=TRUE
        AND e.PROFILE_URL=c.LINKEDIN_URL AND e.CONTACT_UPDATED_AT=c.UPDATED_AT
      ORDER BY e.SOURCE_COMPANY_NAME,c.LAST_NAME,c.FIRST_NAME LIMIT 10001''')
    companies,_,_=directory()
    return {'items':[{**{k.lower():iso(v) for k,v in dict(r).items()},'group_key':storage.group_key(r.get('SOURCE_COMPANY_NAME') or '')} for r in rows[:10000]],'has_more':len(rows)>10000,
            'companies':[{'id_company':c['ID_COMPANY'],'name':c['NAME']} for c in companies if c.get('IS_ACTIVE') is True]}

def reserve_mappings(payload):
    # Reuse existing company matching validation and memory, without publishing
    # any artificial LinkedIn network snapshot or rewriting its latest pointer.
    from core.contact import linkedin_company_rules
    with storage.lock('employer-start'):
        old=latest()
        if old and old['status'] in ('RUNNING','PARTIAL','NEEDS_SNAPSHOT'):raise HTTPException(409,'Terminer ou reprendre le contrôle en cours avant les rapprochements')
        data=pending();available={}
        for row in data['items']:
            if row['status']=='UNMATCHED' and row.get('source_company_name'):
                available.setdefault(storage.group_key(row['source_company_name']),[]).append(row)
        chosen=[];seen=set()
        for value in payload.mappings:
            if value.group_key in seen or value.group_key not in available:raise HTTPException(409,'Rapprochement absent ou modifié ; actualiser')
            seen.add(value.group_key)
            for row in available[value.group_key]:chosen.append((row,value.id_company))
        if not chosen:raise HTTPException(400,'Aucun rapprochement sélectionné')
        synthetic={'id_run':str(uuid.uuid4()),'kind':'EMPLOYER_MATCHING','status':'READY','created_at':storage.now(),'pages':0,
          'rows':[{'First Name':r['first_name'],'Last Name':r['last_name'],'URL':r['profile_url'],'Company':r['source_company_name']} for r,_ in chosen]}
        storage.save(synthetic)
        linkedin_company_rules.match_batch(synthetic['id_run'],payload)
        items=[]
        for row,target in chosen:
            item={'id_contact':row['id_contact'],'name':' '.join([row['first_name'] or '',row['last_name'] or '']).strip(),
              'profile_url':row['profile_url'],'old_company':row.get('id_company'),'old_company_name':row.get('company_name'),
              'expected_updated_at':row['current_updated_at'],'expected_check_run':row['id_run'],
              'op_token':str(uuid.uuid4()),'status':'PENDING','source_name':row['source_company_name'],'source_url':row.get('source_company_url')}
            item['decision']={k:item.get(k) for k in ['id_contact','profile_url','old_company','expected_updated_at','expected_check_run','op_token','source_name','source_url']}
            item['decision'].update(target_company=target,status='MOVED' if target!=item['old_company'] else 'CONFIRMED',reason='Rapprochement société validé par lot')
            items.append(item)
        run={'id_run':str(uuid.uuid4()),'kind':KIND,'mode':'MAPPINGS','status':'RUNNING','created_at':storage.now(),
             'include_network':False,'excluded_network':0,'network_snapshot_at':None,'items':items,'snapshots':[],'error':None,'batch':None}
        save_latest(run)
        return {'id_run':run['id_run'],'queued':True}


def finish(run_id):
    with storage.lock(run_id):
        run=read(run_id)
        for item in run['items']:
            if item['status']=='PENDING':item.update(status='NOT_CHECKED',reason='Contrôle clos manuellement avant vérification')
        run.update(status='COMPLETE',error='Contrôle clos manuellement. Les résultats acquis sont conservés ; certains profils n’ont pas été vérifiés.')
        storage.save(run)
        return {'id_run':run_id,'queued':False}
