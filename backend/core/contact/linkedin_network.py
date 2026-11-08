"""Latest complete CONNECTIONS snapshot, independent from imports and editorial follow."""
import json
from datetime import datetime, timezone
from fastapi import HTTPException
from google.cloud import bigquery
from api.contact.models import linkedin_profile
from core.contact import service as contacts
STATE=f'{contacts.BASE}.RATECARD_CONTACT_LINKEDIN_NETWORK_STATE'
PROFILES=f'{contacts.BASE}.RATECARD_CONTACT_LINKEDIN_NETWORK_PROFILE'
NETWORK_KEY='PRIMARY'

def parse_time(value):
    if isinstance(value,str):value=datetime.fromisoformat(value.replace('Z','+00:00'))
    if not isinstance(value,datetime):raise HTTPException(400,'Date du snapshot absente')
    return value.replace(tzinfo=value.tzinfo or timezone.utc)

def snapshot_source(run):
    # Reopening a saved preview must not make old network data appear recent.
    from core.contact import linkedin_import as m
    seen=set()
    while run.get('parent_run_id'):
        parent=run['parent_run_id']
        if parent in seen or len(seen)>=100:raise HTTPException(400,'Historique de snapshot invalide')
        seen.add(parent);run=m.read(parent)
    return run

def publish_complete(run):
    if run.get('status') not in ('READY','IMPORTED'):raise HTTPException(409,'Seul un snapshot complet peut vérifier le réseau')
    source=snapshot_source(run)
    if source.get('status') not in ('READY','IMPORTED'):raise HTTPException(409,'Le snapshot source n’est pas complet')
    if not source.get('pages') or not source.get('rows'):raise HTTPException(409,'Snapshot complet sans données exploitables')
    observed=parse_time(source.get('created_at'))
    urls=set()
    for row in source['rows']:
        try:url=linkedin_profile(row.get('URL'))
        except (TypeError,ValueError):url=None
        if url:urls.add(url)
    if not urls:raise HTTPException(409,'Aucun profil exploitable ; l’ancien état du réseau est conservé')
    ordered=sorted(urls)
    if len(json.dumps(ordered,ensure_ascii=False).encode())>6_000_000:raise HTTPException(400,'Snapshot réseau trop volumineux pour ce mode de publication')
    with contacts.scope_lock():
        rows=contacts.query(f'''BEGIN TRANSACTION;
          IF @observed >= COALESCE((SELECT MAX(COLLECTED_AT) FROM `{STATE}` WHERE NETWORK_KEY=@key),TIMESTAMP '1970-01-01 00:00:00+00') THEN
            DELETE FROM `{PROFILES}` WHERE NETWORK_KEY=@key;
            INSERT INTO `{PROFILES}` (NETWORK_KEY,PROFILE_URL)
              SELECT @key,url FROM UNNEST(@urls) AS url;
            MERGE `{STATE}` T USING(SELECT @key AS NETWORK_KEY) S ON T.NETWORK_KEY=S.NETWORK_KEY
              WHEN MATCHED THEN UPDATE SET ID_RUN=@run,COLLECTED_AT=@observed,PROFILE_COUNT=@count,UPDATED_AT=CURRENT_TIMESTAMP()
              WHEN NOT MATCHED THEN INSERT(NETWORK_KEY,ID_RUN,COLLECTED_AT,PROFILE_COUNT,UPDATED_AT)
                VALUES(@key,@run,@observed,@count,CURRENT_TIMESTAMP());
          END IF;
          COMMIT TRANSACTION;
          SELECT ID_RUN,COLLECTED_AT,PROFILE_COUNT FROM `{STATE}` WHERE NETWORK_KEY=@key;''',
          [contacts.p('key','STRING',NETWORK_KEY),contacts.p('run','STRING',source['id_run']),contacts.p('observed','TIMESTAMP',observed),
           contacts.p('count','INT64',len(ordered)),bigquery.ArrayQueryParameter('urls','STRING',ordered)])
    return {'snapshot_id':rows[0]['ID_RUN'],'collected_at':parse_time(rows[0]['COLLECTED_AT']).isoformat(),'profile_count':int(rows[0]['PROFILE_COUNT'])}

def publish_saved_snapshot(run_id):
    """One-off seeding for a previously complete preview; no LinkedIn call or contact edit."""
    from core.contact import linkedin_import as m
    with m.lock(run_id):return publish_complete(m.read(run_id))
