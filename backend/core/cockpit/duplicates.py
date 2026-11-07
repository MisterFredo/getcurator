"""Source URL duplicates: deterministic candidates and atomic deletion."""
from fastapi import HTTPException
from google.cloud import bigquery
from config import BQ_PROJECT, BQ_DATASET
from utils.bigquery_utils import get_bigquery_client, query_bq
BASE=f'{BQ_PROJECT}.{BQ_DATASET}'
CONTENT=f'{BASE}.RATECARD_CONTENT'
RELATIONS=['RATECARD_CONTENT_COMPANY','RATECARD_CONTENT_SOLUTION','RATECARD_CONTENT_TOPIC','RATECARD_CONTENT_CONCEPT','RATECARD_CONTENT_ENRICHED']
# Exact source URL after trimming surrounding whitespace. No tracking/query/path
# normalization: two deliberately different URLs remain distinct.
RANKED=f"""
 SELECT ID_CONTENT, TITLE, SOURCE_URL, PUBLISHED_AT, CREATED_AT,
 ROW_NUMBER() OVER (PARTITION BY TRIM(SOURCE_URL)
   ORDER BY PUBLISHED_AT DESC, CREATED_AT DESC, ID_CONTENT ASC) AS rn,
 FIRST_VALUE(ID_CONTENT) OVER (PARTITION BY TRIM(SOURCE_URL)
   ORDER BY PUBLISHED_AT DESC, CREATED_AT DESC, ID_CONTENT ASC) AS KEPT_ID_CONTENT,
 FIRST_VALUE(TITLE) OVER (PARTITION BY TRIM(SOURCE_URL)
   ORDER BY PUBLISHED_AT DESC, CREATED_AT DESC, ID_CONTENT ASC) AS KEPT_TITLE
 FROM `{CONTENT}` WHERE NULLIF(TRIM(SOURCE_URL),'') IS NOT NULL
"""

def get_duplicate_urls():
    return query_bq(f'WITH ranked AS ({RANKED}) SELECT * FROM ranked WHERE rn > 1 ORDER BY SOURCE_URL, rn')

def delete_duplicate_url(content_id):
    if not isinstance(content_id,str) or not content_id.strip():raise HTTPException(400,'Identifiant requis')
    # Check and all deletes share the same transactional snapshot. On a stale
    # candidate the script does nothing and returns no deletion, never HTTP 200 error.
    deletes='\n'.join(f'DELETE FROM `{BASE}.{table}` WHERE ID_CONTENT=@id;' for table in RELATIONS)
    sql=f"""
    BEGIN TRANSACTION;
    CREATE TEMP TABLE candidates AS {RANKED};
    IF EXISTS(SELECT 1 FROM candidates WHERE ID_CONTENT=@id AND rn > 1 AND KEPT_ID_CONTENT != @id) THEN
      {deletes}
      DELETE FROM `{CONTENT}` WHERE ID_CONTENT=@id;
      SELECT @id AS deleted_id;
    ELSE
      SELECT CAST(NULL AS STRING) AS deleted_id;
    END IF;
    COMMIT TRANSACTION;
    """
    # Use a declared variable and final SELECT: BQ script result must be its final statement.
    sql=sql.replace('BEGIN TRANSACTION;','DECLARE deleted STRING DEFAULT NULL;\nBEGIN TRANSACTION;',1).replace('SELECT @id AS deleted_id;','SET deleted=@id;').replace('SELECT CAST(NULL AS STRING) AS deleted_id;','SET deleted=NULL;')+'\nSELECT deleted AS deleted_id;'
    try:
        rows=list(get_bigquery_client().query(sql,job_config=bigquery.QueryJobConfig(query_parameters=[bigquery.ScalarQueryParameter('id','STRING',content_id.strip())])).result())
    except Exception as exc:
        import logging
        logging.getLogger(__name__).exception('Duplicate deletion transaction failed')
        raise HTTPException(500,'Suppression impossible ; aucune suppression partielle validée') from exc
    if not rows or not rows[0]['deleted_id']:raise HTTPException(409,'Ce contenu n’est plus un doublon supprimable. Actualisez le contrôle.')
    return {'status':'ok','deleted_id':content_id.strip(),'message':'Doublon supprimé.'}


def delete_duplicate_urls(content_ids):
    if not isinstance(content_ids,list) or not content_ids or len(content_ids)>10000:
        raise HTTPException(400,'Fournir de 1 à 10000 identifiants')
    if any(not isinstance(value,str) or not value.strip() or len(value)>200 for value in content_ids):
        raise HTTPException(400,'Identifiant invalide')
    ids=list(dict.fromkeys(value.strip() for value in content_ids))
    deletes='\n'.join(f'DELETE FROM `{BASE}.{table}` WHERE ID_CONTENT IN (SELECT ID_CONTENT FROM approved);' for table in RELATIONS)
    sql=f"""
    DECLARE deleted_ids ARRAY<STRING> DEFAULT [];
    BEGIN TRANSACTION;
    CREATE TEMP TABLE candidates AS {RANKED};
    CREATE TEMP TABLE approved AS
      SELECT DISTINCT c.ID_CONTENT FROM candidates c
      WHERE c.ID_CONTENT IN UNNEST(@ids) AND c.rn > 1
        AND c.KEPT_ID_CONTENT != c.ID_CONTENT
        AND NOT EXISTS (
          SELECT 1 FROM candidates k WHERE k.ID_CONTENT=c.ID_CONTENT AND k.rn=1
        );
    SET deleted_ids=ARRAY(SELECT ID_CONTENT FROM approved ORDER BY ID_CONTENT);
    IF ARRAY_LENGTH(deleted_ids)>0 THEN
      {deletes}
      DELETE FROM `{CONTENT}` WHERE ID_CONTENT IN (SELECT ID_CONTENT FROM approved);
    END IF;
    COMMIT TRANSACTION;
    SELECT deleted_ids,
      ARRAY(SELECT id FROM UNNEST(@ids) id
            WHERE id NOT IN UNNEST(deleted_ids) ORDER BY id) AS skipped_ids;
    """
    try:
        rows=list(get_bigquery_client().query(sql,job_config=bigquery.QueryJobConfig(
            query_parameters=[bigquery.ArrayQueryParameter('ids','STRING',ids)]
        )).result())
    except Exception as exc:
        import logging
        logging.getLogger(__name__).exception('Batch duplicate deletion transaction failed')
        raise HTTPException(500,'Échec de la transaction de suppression. Actualisez le contrôle pour vérifier l’état réel avant de réessayer.') from exc
    if not rows:
        raise HTTPException(500,'Confirmation de suppression indisponible. Actualisez le contrôle avant de réessayer.')
    deleted=list(rows[0]['deleted_ids'] or [])
    skipped=list(rows[0]['skipped_ids'] or [])
    return {'status':'ok','requested':len(ids),'deleted_count':len(deleted),'deleted_ids':deleted,
            'skipped_count':len(skipped),'skipped_ids':skipped,
            'message':f'{len(deleted)} doublon(s) supprimé(s) · {len(skipped)} identifiant(s) non supprimable(s) ignoré(s).'}
