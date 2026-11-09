"""CSV -> staged preview -> insert-only resumable batches. No network verification."""
import csv
import io
import json
import logging
import uuid
from datetime import datetime,timezone
from fastapi import HTTPException
from api.contact.models import ContactCreate
from core.contact import service as contacts
from core.contact import linkedin_import as storage
from core.contact.company_follow import sync_sql

log=logging.getLogger(__name__)
HEADERS={'first_name','last_name','company_name','job_title','email','linkedin_url','sales_navigator_url','source_full_name'}
REQUIRED={'first_name','last_name','company_name','linkedin_url'}

def parse(text):
    text=text.lstrip('\ufeff')
    if len(text.encode('utf-8'))>3_000_000:raise HTTPException(400,'CSV limité à 3 Mo')
    try:
        try:delimiter=csv.Sniffer().sniff(text[:8192],delimiters=',;\t').delimiter
        except csv.Error:delimiter=','
        reader=csv.DictReader(io.StringIO(text),delimiter=delimiter,strict=True)
        fields=[str(x).strip().lower() for x in reader.fieldnames or []]
        if len(set(fields))!=len(fields) or not REQUIRED.issubset(fields) or set(fields)-HEADERS:
            raise HTTPException(400,'En-têtes attendus : first_name,last_name,company_name,job_title,email,linkedin_url,sales_navigator_url (source_full_name facultatif)')
        reader.fieldnames=fields;result=[]
        for n,raw in enumerate(reader,2):
            if n>2001:raise HTTPException(400,'Maximum 2 000 contacts par fichier')
            if None in raw or any(v is None for v in raw.values()):raise HTTPException(400,f'Ligne {n} : nombre de colonnes invalide')
            row={k:v.strip() for k,v in raw.items()}
            if not any(row.values()):continue
            result.append({'line':n,'company_name':row.get('company_name',''),'raw':row})
    except csv.Error as exc:raise HTTPException(400,'CSV invalide') from exc
    if not result:raise HTTPException(400,'CSV vide')
    return result

def read(run_id):
    run=storage.read(run_id)
    if run.get('kind')!='CONTACT_CSV':raise HTTPException(404,'Import CSV introuvable')
    return run

def existing_index():
    rows=contacts.query(f'SELECT ID_CONTACT,LINKEDIN_URL,EMAIL FROM `{contacts.CONTACT}`')
    profiles={};emails={}
    from api.contact.models import linkedin_profile
    for row in rows:
        try:url=linkedin_profile(row.get('LINKEDIN_URL'))
        except ValueError:url=None
        if url:profiles[url]=row['ID_CONTACT']
        if row.get('EMAIL'):emails[str(row['EMAIL']).strip().casefold()]=row['ID_CONTACT']
    return profiles,emails

def preview(text):
    rows=parse(text)
    companies,aliases,remembered=storage.directory()
    names,index,memory=storage.matching(companies,aliases,remembered)
    profiles,emails=existing_index()
    by_profile={};by_email={}
    for item in rows:
        item.update(status='INVALID',reason='',id_company=None)
        try:
            raw=item['raw']
            if not raw.get('company_name'):raise ValueError('Société manquante')
            if not raw.get('linkedin_url'):raise ValueError('URL de profil LinkedIn manquante')
            payload=ContactCreate(**{k:raw.get(k) or None for k in ['email','job_title','linkedin_url','sales_navigator_url']},first_name=raw.get('first_name',''),last_name=raw.get('last_name',''))
            item['data']=payload.dict()
            matches=set(index.get(storage.normalized(raw['company_name']),set()))
            matches.update(memory.get(storage.group_key(raw['company_name']),set()))
            item['id_company']=next(iter(matches)) if len(matches)==1 else None
            item['status']='NEW' if item['id_company'] else 'UNMATCHED'
            url=payload.linkedin_url;email=payload.email
            if url in profiles:
                item.update(status='EXISTS',reason='Profil déjà présent : fiche existante conservée',id_contact=profiles[url])
            elif email and email in emails:
                item.update(status='CONFLICT',reason='E-mail déjà associé à un contact ; vérifier sa fiche avant import')
            by_profile.setdefault(url,[]).append(item)
            if email:by_email.setdefault(email,[]).append(item)
        except (ValueError,TypeError) as exc:
            item['reason']=str(exc)[:700]
    for group in list(by_profile.values())+list(by_email.values()):
        if len(group)>1:
            for row in group:
                if row['status']!='EXISTS':row.update(status='CONFLICT',reason='Profil ou e-mail répété dans le fichier : corriger avant import')
    run={'id_run':str(uuid.uuid4()),'kind':'CONTACT_CSV','status':'READY','created_at':storage.now(),'rows':rows,
         'companies':[{'id_company':i,'name':name} for i,name in sorted(names.items(),key=lambda x:x[1])],
         'processed':0,'imported':0,'skipped':0,'error':None}
    storage.save(run)
    return status(run['id_run'])

def status(run_id):
    run=read(run_id)
    return {k:run.get(k) for k in ['id_run','status','rows','companies','created_at','updated_at','processed','imported','skipped','error','selected_count']}

def reserve(run_id,selections):
    with storage.lock(run_id):
        run=read(run_id)
        if run['status']!='READY':return {'id_run':run_id,'queued':False,'status':run['status']}
        rows={r['line']:r for r in run['rows']};seen=set();prepared=[]
        active={r['ID_COMPANY'] for r in contacts.query(f'SELECT ID_COMPANY FROM `{contacts.COMPANY}` WHERE IS_ACTIVE=TRUE')}
        for choice in selections:
            row=rows.get(choice.line)
            if choice.line in seen or not row or row['status'] not in ('NEW','UNMATCHED'):raise HTTPException(409,'Sélection invalide ; recharger l’aperçu')
            if choice.id_company not in active:raise HTTPException(409,'Société absente ou inactive')
            seen.add(choice.line)
            data=dict(row['data']);data.update(id_company=choice.id_company,
                id_contact=str(uuid.uuid5(uuid.NAMESPACE_URL,contacts.BASE+'|linkedin|'+data['linkedin_url'])),id_affiliation=str(uuid.uuid4()))
            prepared.append(data)
        if not prepared:raise HTTPException(400,'Aucun contact sélectionné')
        run.update(status='IMPORTING',prepared=prepared,selected_count=len(prepared),processed=0,error=None)
        storage.save(run)
        return {'id_run':run_id,'queued':True,'status':'IMPORTING'}

def write_batch(run_id,batch):
    return contacts.query(f'''CREATE TEMP TABLE incoming AS
      SELECT JSON_VALUE(j,'$.id_contact') ID_CONTACT,JSON_VALUE(j,'$.id_affiliation') ID_AFFILIATION,
        JSON_VALUE(j,'$.first_name') FIRST_NAME,JSON_VALUE(j,'$.last_name') LAST_NAME,
        JSON_VALUE(j,'$.email') EMAIL,JSON_VALUE(j,'$.job_title') JOB_TITLE,
        JSON_VALUE(j,'$.linkedin_url') LINKEDIN_URL,JSON_VALUE(j,'$.sales_navigator_url') SALES_NAVIGATOR_URL,
        JSON_VALUE(j,'$.id_company') ID_COMPANY
      FROM UNNEST(JSON_QUERY_ARRAY(PARSE_JSON(@rows))) j;
      BEGIN TRANSACTION;
      ASSERT NOT EXISTS(SELECT 1 FROM incoming i LEFT JOIN `{contacts.COMPANY}` co ON co.ID_COMPANY=i.ID_COMPANY
        WHERE co.ID_COMPANY IS NULL OR co.IS_ACTIVE IS DISTINCT FROM TRUE) AS 'Une société est absente ou inactive';
      CREATE TEMP TABLE new_contacts AS SELECT i.* FROM incoming i
        WHERE NOT EXISTS(SELECT 1 FROM `{contacts.CONTACT}` c WHERE c.ID_CONTACT=i.ID_CONTACT)
        AND NOT EXISTS(SELECT 1 FROM `{contacts.CONTACT}` c WHERE LOWER(RTRIM(c.LINKEDIN_URL,'/'))=i.LINKEDIN_URL)
        AND NOT EXISTS(SELECT 1 FROM `{contacts.CONTACT}` c WHERE LOWER(c.EMAIL)=i.EMAIL);
      INSERT INTO `{contacts.CONTACT}`(ID_CONTACT,FIRST_NAME,LAST_NAME,EMAIL,JOB_TITLE,LINKEDIN_URL,SALES_NAVIGATOR_URL,
        IS_ACTIVE,CREATED_AT,UPDATED_AT,IMPORT_SOURCE,IMPORT_RUN_ID,LINKEDIN_PROFILE_UPDATED_AT)
        SELECT ID_CONTACT,FIRST_NAME,LAST_NAME,EMAIL,JOB_TITLE,LINKEDIN_URL,SALES_NAVIGATOR_URL,
          TRUE,CURRENT_TIMESTAMP(),CURRENT_TIMESTAMP(),'CSV',@run,CURRENT_TIMESTAMP() FROM new_contacts;
      INSERT INTO `{contacts.AFFILIATION}`(ID_CONTACT_COMPANY,ID_CONTACT,ID_COMPANY,JOB_TITLE,STARTED_AT,ENDED_AT,CREATED_AT,UPDATED_AT)
        SELECT ID_AFFILIATION,ID_CONTACT,ID_COMPANY,JOB_TITLE,CURRENT_TIMESTAMP(),NULL,CURRENT_TIMESTAMP(),CURRENT_TIMESTAMP() FROM new_contacts;
      {sync_sql('c.ID_CONTACT IN (SELECT ID_CONTACT FROM new_contacts)')}
      COMMIT TRANSACTION;
      SELECT COUNT(*) AS IMPORTED FROM `{contacts.CONTACT}` WHERE IMPORT_RUN_ID=@run AND ID_CONTACT IN(SELECT ID_CONTACT FROM incoming);''',
      [contacts.p('rows','STRING',json.dumps(batch,ensure_ascii=False)),contacts.p('run','STRING',run_id)])[0]['IMPORTED']

def apply(run_id):
    with storage.lock(run_id):
        run=read(run_id)
        if run['status']!='IMPORTING':return
        try:
            while run['processed']<len(run['prepared']):
                batch=run['prepared'][run['processed']:run['processed']+250]
                with contacts.scope_lock():count=int(write_batch(run_id,batch))
                run['processed']+=len(batch);run['imported']+=count;run['skipped']+=len(batch)-count
                storage.save(run)
            run.update(status='COMPLETE',error=None);storage.save(run)
        except Exception:
            log.exception('CSV contacts import failed run=%s',run_id)
            run.update(status='PARTIAL',error='Écriture interrompue. Les lots validés sont conservés ; reprendre cet import.');storage.save(run)

def resume(run_id):
    with storage.lock(run_id):
        run=read(run_id)
        if run['status']=='COMPLETE':return {'id_run':run_id,'queued':False,'status':'COMPLETE'}
        if run['status'] not in ('IMPORTING','PARTIAL') or not run.get('prepared'):raise HTTPException(409,'Aucun import à reprendre')
        run.update(status='IMPORTING',error=None);storage.save(run)
        return {'id_run':run_id,'queued':True,'status':'IMPORTING'}
