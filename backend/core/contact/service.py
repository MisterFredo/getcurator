"""Contact identity + company affiliation + one shared LinkedIn collection point.

No USER writes, no collection trigger, no provider calls. One write transaction.
"""
from __future__ import annotations
from datetime import datetime,timezone
import hashlib
import json
import uuid
from fastapi import HTTPException
from google.cloud import bigquery
from config import BQ_PROJECT,BQ_DATASET
from utils.bigquery_utils import get_bigquery_client
from api.contact.models import ContactCreate,ContactUpdate,ContactFollowUpdate,linkedin_profile

BASE=f'{BQ_PROJECT}.{BQ_DATASET}'
CONTACT=f'{BASE}.RATECARD_CONTACT'
AFFILIATION=f'{BASE}.RATECARD_CONTACT_COMPANY'
COMPANY=f'{BASE}.RATECARD_COMPANY'
WATCH=f'{BASE}.RATECARD_COMPANY_WATCH'
NETWORK_STATE=f'{BASE}.RATECARD_CONTACT_LINKEDIN_NETWORK_STATE'
NETWORK_PROFILE=f'{BASE}.RATECARD_CONTACT_LINKEDIN_NETWORK_PROFILE'

def query(sql,params=()):return list(get_bigquery_client().query(sql,job_config=bigquery.QueryJobConfig(query_parameters=list(params))).result())
def p(name,kind,value):return bigquery.ScalarQueryParameter(name,kind,value)
def scope_lock():
    # Lazy import avoids a models -> contact -> watch -> models import cycle.
    from core.library.company_watch_library import document_lock
    return document_lock('contacts-'+hashlib.sha256(BASE.encode()).hexdigest())

READ=f"""SELECT c.*,a.ID_COMPANY,co.NAME AS COMPANY_NAME,co.IS_ACTIVE AS COMPANY_IS_ACTIVE,
  CASE WHEN c.IMPORT_SOURCE='LINKEDIN_CONNECTIONS' THEN 'LINKEDIN_IMPORT'
    WHEN NULLIF(TRIM(c.IMPORT_SOURCE),'') IS NULL OR c.IMPORT_SOURCE='MANUAL' THEN 'MANUAL'
    ELSE 'OTHER' END AS CONTACT_ORIGIN,
  CASE WHEN NULLIF(TRIM(c.LINKEDIN_URL),'') IS NULL THEN 'NOT_VERIFIED'
    WHEN np.PROFILE_URL IS NOT NULL THEN 'CONFIRMED'
    WHEN ns.COLLECTED_AT >= COALESCE(c.LINKEDIN_PROFILE_UPDATED_AT,c.CREATED_AT) THEN 'NOT_FOUND'
    ELSE 'NOT_VERIFIED' END AS NETWORK_STATUS,
  CASE WHEN NULLIF(TRIM(c.LINKEDIN_URL),'') IS NOT NULL AND
      (np.PROFILE_URL IS NOT NULL OR ns.COLLECTED_AT >= COALESCE(c.LINKEDIN_PROFILE_UPDATED_AT,c.CREATED_AT))
    THEN ns.COLLECTED_AT ELSE NULL END AS NETWORK_CHECKED_AT,
  w.ID_COMPANY_WATCH,COALESCE(w.IS_ACTIVE,FALSE) AS LINKEDIN_FOLLOW_ENABLED
  FROM `{CONTACT}` c
  LEFT JOIN `{NETWORK_STATE}` ns ON ns.NETWORK_KEY='PRIMARY'
  LEFT JOIN `{NETWORK_PROFILE}` np ON np.NETWORK_KEY='PRIMARY' AND np.PROFILE_URL=c.LINKEDIN_URL
  LEFT JOIN `{AFFILIATION}` a ON a.ID_CONTACT=c.ID_CONTACT AND a.ENDED_AT IS NULL
  LEFT JOIN `{COMPANY}` co ON co.ID_COMPANY=a.ID_COMPANY
  LEFT JOIN `{WATCH}` w ON w.ID_CONTACT=c.ID_CONTACT AND w.ID_COMPANY=a.ID_COMPANY
    AND w.SOURCE_URL=c.LINKEDIN_URL
  QUALIFY ROW_NUMBER() OVER(PARTITION BY c.ID_CONTACT ORDER BY w.IS_ACTIVE DESC,w.UPDATED_AT DESC,w.ID_COMPANY_WATCH)=1"""

def out(row):
    value={k.lower():v for k,v in dict(row).items()}
    value['display_name']=' '.join(x for x in [value.get('first_name'),value.get('last_name')] if x)
    value['linkedin_follow_enabled']=bool(value.get('linkedin_follow_enabled'))
    return value

def get_contact(contact_id):
    rows=query(f'WITH contacts AS ({READ}) SELECT * FROM contacts WHERE ID_CONTACT=@id',[p('id','STRING',contact_id)])
    if not rows:raise HTTPException(404,'Contact introuvable')
    return out(rows[0])

def list_contacts(company_id=None,text=None,offset=0,limit=50):
    if offset<0 or not 1<=limit<=200:raise HTTPException(400,'Pagination invalide')
    where=['TRUE'];params=[p('offset','INT64',offset),p('limit','INT64',limit)]
    if company_id:where.append('ID_COMPANY=@company');params.append(p('company','STRING',company_id))
    if text and text.strip():
        where.append("CONTAINS_SUBSTR(CONCAT(COALESCE(FIRST_NAME,''),' ',COALESCE(LAST_NAME,''),' ',COALESCE(EMAIL,''),' ',COALESCE(COMPANY_NAME,''),' ',COALESCE(JOB_TITLE,'')),@q)")
        params.append(p('q','STRING',text.strip()))
    rows=query(f"""WITH contacts AS ({READ}),filtered AS(SELECT * FROM contacts WHERE {' AND '.join(where)})
      SELECT (SELECT COUNT(*) FROM filtered) AS TOTAL,
      ARRAY(SELECT AS STRUCT * FROM filtered ORDER BY LOWER(LAST_NAME),LOWER(FIRST_NAME),ID_CONTACT LIMIT @limit OFFSET @offset) AS ITEMS""",params)
    result=dict(rows[0]) if rows else {'TOTAL':0,'ITEMS':[]}
    return {'status':'ok','contacts':[out(row) for row in result['ITEMS']], 'total':int(result['TOTAL']),
            'has_more':offset+limit<int(result['TOTAL']),'offset':offset,'limit':limit}

def company_history(contact_id):
    get_contact(contact_id)
    rows=query(f"""SELECT a.*,c.NAME AS COMPANY_NAME FROM `{AFFILIATION}` a
      LEFT JOIN `{COMPANY}` c ON c.ID_COMPANY=a.ID_COMPANY
      WHERE ID_CONTACT=@id ORDER BY STARTED_AT DESC,ID_CONTACT_COMPANY""",[p('id','STRING',contact_id)])
    return {'status':'ok','companies':[{k.lower():v for k,v in dict(row).items()} for row in rows]}

def plan(existing,changes,contact_id):
    keys=['first_name','last_name','email','linkedin_url','sales_navigator_url','id_company','job_title','is_active','linkedin_follow_enabled']
    values={k:existing.get(k) for k in keys} if existing else {}
    values.update({k:v for k,v in changes.items() if k in keys})
    if values.get('is_active') is False:
        if changes.get('linkedin_follow_enabled') is True:raise HTTPException(422,'Un contact inactif ne peut pas être suivi')
        values['linkedin_follow_enabled']=False
    try:validated=ContactCreate(**values)
    except ValueError as exc:raise HTTPException(422,str(exc)) from exc
    data=validated.dict()
    watch_id=str(uuid.uuid5(uuid.NAMESPACE_URL,json.dumps([BASE,contact_id,data['id_company'],data['linkedin_url']],ensure_ascii=False))) if data['linkedin_follow_enabled'] else None
    return data,watch_id

def _check(data,contact_id):
    if data['id_company']:
        companies=query(f'SELECT IS_ACTIVE FROM `{COMPANY}` WHERE ID_COMPANY=@company LIMIT 1',[p('company','STRING',data['id_company'])])
        if not companies:raise HTTPException(404,'Société introuvable')
        if data['linkedin_follow_enabled'] and not companies[0]['IS_ACTIVE']:raise HTTPException(409,'La société doit être active pour activer le suivi')
    if data['email'] or data['linkedin_url']:
        duplicate=query(f"""SELECT ID_CONTACT FROM `{CONTACT}` WHERE ID_CONTACT!=@id AND
          ((@email IS NOT NULL AND LOWER(EMAIL)=@email) OR (@linkedin IS NOT NULL AND LINKEDIN_URL=@linkedin)) LIMIT 1""",
          [p('id','STRING',contact_id),p('email','STRING',data['email']),p('linkedin','STRING',data['linkedin_url'])])
        if duplicate:raise HTTPException(409,'Un contact possède déjà cet e-mail ou ce profil LinkedIn ; modifier sa fiche existante')
    if data['linkedin_follow_enabled']:
        points=query(f"SELECT ID_COMPANY_WATCH,ID_CONTACT,SOURCE_URL FROM `{WATCH}` WHERE ID_COMPANY=@company",[p('company','STRING',data['id_company'])])
        for point in points:
            if point.get('ID_CONTACT')==contact_id:continue
            try:matches=linkedin_profile(point.get('SOURCE_URL'))==data['linkedin_url']
            except ValueError:matches=False
            if matches:raise HTTPException(409,'Ce profil possède déjà un point de collecte pour cette société ; nettoyer le point existant avant de créer le suivi Contact')

def _write(contact_id,data,watch_id):
    display=' '.join(x for x in [data['first_name'],data['last_name']] if x)
    params=[p('id','STRING',contact_id),p('first','STRING',data['first_name']),p('last','STRING',data['last_name']),
      p('email','STRING',data['email']),p('linkedin','STRING',data['linkedin_url']),p('sales','STRING',data.get('sales_navigator_url')),p('company','STRING',data['id_company']),
      p('job','STRING',data['job_title']),p('active','BOOL',data['is_active']),p('watch','STRING',watch_id),
      p('label','STRING',f'LinkedIn — {display}'),p('author','STRING',display),p('affiliation','STRING',str(uuid.uuid4()))]
    query(f"""BEGIN TRANSACTION;
    MERGE `{CONTACT}` T USING(SELECT @id AS ID_CONTACT) S ON T.ID_CONTACT=S.ID_CONTACT
      WHEN MATCHED THEN UPDATE SET FIRST_NAME=@first,LAST_NAME=@last,EMAIL=@email,LINKEDIN_PROFILE_UPDATED_AT=IF(LINKEDIN_URL IS DISTINCT FROM @linkedin,CURRENT_TIMESTAMP(),LINKEDIN_PROFILE_UPDATED_AT),LINKEDIN_URL=@linkedin,SALES_NAVIGATOR_URL=@sales,JOB_TITLE=@job,IS_ACTIVE=@active,UPDATED_AT=CURRENT_TIMESTAMP()
      WHEN NOT MATCHED THEN INSERT(ID_CONTACT,FIRST_NAME,LAST_NAME,EMAIL,LINKEDIN_URL,JOB_TITLE,IS_ACTIVE,CREATED_AT,UPDATED_AT,IMPORT_SOURCE,LINKEDIN_PROFILE_UPDATED_AT,SALES_NAVIGATOR_URL)
        VALUES(@id,@first,@last,@email,@linkedin,@job,@active,CURRENT_TIMESTAMP(),CURRENT_TIMESTAMP(),'MANUAL',IF(@linkedin IS NULL,NULL,CURRENT_TIMESTAMP()),@sales);
    UPDATE `{AFFILIATION}` SET ENDED_AT=CURRENT_TIMESTAMP(),UPDATED_AT=CURRENT_TIMESTAMP()
      WHERE ID_CONTACT=@id AND ENDED_AT IS NULL AND (@company IS NULL OR ID_COMPANY!=@company);
    IF @company IS NOT NULL THEN
      MERGE `{AFFILIATION}` T USING(SELECT @id AS ID_CONTACT,@company AS ID_COMPANY) S
        ON T.ID_CONTACT=S.ID_CONTACT AND T.ID_COMPANY=S.ID_COMPANY AND T.ENDED_AT IS NULL
        WHEN MATCHED THEN UPDATE SET JOB_TITLE=@job,UPDATED_AT=CURRENT_TIMESTAMP()
        WHEN NOT MATCHED THEN INSERT(ID_CONTACT_COMPANY,ID_CONTACT,ID_COMPANY,JOB_TITLE,STARTED_AT,ENDED_AT,CREATED_AT,UPDATED_AT)
          VALUES(@affiliation,@id,@company,@job,CURRENT_TIMESTAMP(),NULL,CURRENT_TIMESTAMP(),CURRENT_TIMESTAMP());
    END IF;
    UPDATE `{WATCH}` SET IS_ACTIVE=FALSE,UPDATED_AT=CURRENT_TIMESTAMP()
      WHERE ID_CONTACT=@id AND IS_ACTIVE=TRUE AND (@watch IS NULL OR ID_COMPANY_WATCH!=@watch);
    IF @watch IS NOT NULL THEN
      MERGE `{WATCH}` T USING(SELECT @watch AS ID_COMPANY_WATCH) S ON T.ID_COMPANY_WATCH=S.ID_COMPANY_WATCH
        WHEN MATCHED THEN UPDATE SET IS_ACTIVE=TRUE,LABEL=@label,AUTHOR_NAME=@author,UPDATED_AT=CURRENT_TIMESTAMP()
        WHEN NOT MATCHED THEN INSERT(ID_COMPANY_WATCH,ID_COMPANY,ID_CONTACT,LABEL,SOURCE_TYPE,SOURCE_URL,SOURCE_ROLE,AUTHOR_NAME,COLLECTION_METHOD,COLLECTION_CONFIG,IS_ACTIVE,CREATED_AT,UPDATED_AT)
          VALUES(@watch,@company,@id,@label,'LINKEDIN',@linkedin,'EMPLOYEE',@author,'BRIGHTDATA',PARSE_JSON('{{}}'),TRUE,CURRENT_TIMESTAMP(),CURRENT_TIMESTAMP());
    END IF;
    COMMIT TRANSACTION;""",params)

def create_contact(payload):
    contact_id=str(uuid.uuid4())
    with scope_lock():
        changes=payload.dict(exclude_unset=True)
        if 'linkedin_follow_enabled' not in changes:
            from core.contact.company_follow import default_follow
            changes['linkedin_follow_enabled']=default_follow(changes.get('id_company'),changes.get('linkedin_url'),changes.get('is_active',True))
        data,watch_id=plan(None,changes,contact_id);_check(data,contact_id);_write(contact_id,data,watch_id)
        return {'status':'ok','contact':get_contact(contact_id)}

def update_contact(contact_id,payload):
    with scope_lock():
        existing=get_contact(contact_id);changes=payload.dict(exclude_unset=True)
        expected=changes.pop('expected_updated_at',None)
        if expected is not None:
            actual=existing['updated_at'];actual=datetime.fromisoformat(actual.replace('Z','+00:00')) if isinstance(actual,str) else actual
            if actual.replace(tzinfo=actual.tzinfo or timezone.utc)!=expected.replace(tzinfo=expected.tzinfo or timezone.utc):raise HTTPException(409,'Ce contact a changé ; recharger la fiche avant de sauvegarder')
        if not changes:raise HTTPException(400,'Aucune modification fournie')
        data,watch_id=plan(existing,changes,contact_id);_check(data,contact_id);_write(contact_id,data,watch_id)
        return {'status':'ok','contact':get_contact(contact_id)}

def set_follow(contact_id,payload,expected_watch_id=None):
    # Company checks and the update are under one shared mutation lock. Call the
    # internal write rather than recursively acquiring the same GCS lease.
    with scope_lock():
        existing=get_contact(contact_id)
        if expected_watch_id is not None and existing.get('id_company_watch')!=expected_watch_id:raise HTTPException(409,'Ce point appartient à un ancien rattachement ; modifier le suivi depuis la fiche Contact actuelle')
        if payload.expected_company_id and existing.get('id_company')!=payload.expected_company_id:raise HTTPException(409,'Le contact a changé de société ; actualiser la liste')
        if payload.expected_updated_at is not None:
            actual=existing['updated_at'];actual=datetime.fromisoformat(actual.replace('Z','+00:00')) if isinstance(actual,str) else actual
            if actual.replace(tzinfo=actual.tzinfo or timezone.utc)!=payload.expected_updated_at.replace(tzinfo=payload.expected_updated_at.tzinfo or timezone.utc):raise HTTPException(409,'Le suivi a changé ; actualiser la liste')
        data,watch_id=plan(existing,{'linkedin_follow_enabled':payload.is_enabled},contact_id)
        _check(data,contact_id);_write(contact_id,data,watch_id)
        return {'status':'ok','contact':get_contact(contact_id)}
