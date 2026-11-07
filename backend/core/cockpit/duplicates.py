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
