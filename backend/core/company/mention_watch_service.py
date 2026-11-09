"""Company eligibility for external News mentions. No collection scheduling here."""
from fastapi import HTTPException
from config import BQ_PROJECT, BQ_DATASET
from utils.bigquery_utils import query_bq

COMPANY = f'{BQ_PROJECT}.{BQ_DATASET}.RATECARD_COMPANY'
CONFIG = f'{BQ_PROJECT}.{BQ_DATASET}.RATECARD_COMPANY_MENTION_CONFIG'


def enabled_company_ids():
    """One set-based lookup for the whole company list, never one lookup per row."""
    rows = query_bq(f'SELECT ID_COMPANY FROM `{CONFIG}` WHERE IS_ENABLED=TRUE')
    return {row['ID_COMPANY'] for row in rows}


def get_mention_watch_config(company_id):
    rows = query_bq(f'''SELECT c.ID_COMPANY, c.NAME, c.IS_ACTIVE,
        COALESCE(m.IS_ENABLED,FALSE) AS IS_ENABLED, m.CREATED_AT, m.UPDATED_AT
        FROM `{COMPANY}` c LEFT JOIN `{CONFIG}` m ON m.ID_COMPANY=c.ID_COMPANY
        WHERE c.ID_COMPANY=@company LIMIT 1''', {'company':company_id})
    if not rows:
        raise HTTPException(404,'Société introuvable')
    row = rows[0]
    return {'id_company':row['ID_COMPANY'],'company_name':row['NAME'],
            'is_active':row.get('IS_ACTIVE') is True,'is_enabled':row.get('IS_ENABLED') is True,
            'created_at':row.get('CREATED_AT'),'updated_at':row.get('UPDATED_AT')}


def set_mention_watch_config(company_id, is_enabled):
    if type(is_enabled) is not bool:
        raise ValueError('is_enabled doit être un booléen')
    # Reuse the distributed lease already installed with Library. Serialize two
    # concurrent first activations because BigQuery does not enforce uniqueness.
    from core.library.company_watch_library import document_lock
    import hashlib
    lock_key = 'mention-config-' + hashlib.sha256((COMPANY+':'+company_id).encode()).hexdigest()
    from core.contact import service as contacts
    from core.contact.company_follow import sync_sql
    with contacts.scope_lock(), document_lock(lock_key):
        current = get_mention_watch_config(company_id)
        if is_enabled and not current['is_active']:
            raise HTTPException(409,'Impossible d’activer la veille d’une société inactive')
        if current['is_enabled'] == is_enabled:
            return current
        enabled_sql = 'TRUE' if is_enabled else 'FALSE'  # fixed literals, never user text
        query_bq(f'''BEGIN TRANSACTION;
            MERGE `{CONFIG}` T
            USING (SELECT ID_COMPANY FROM `{COMPANY}`
                   WHERE ID_COMPANY=@company AND (IS_ACTIVE=TRUE OR {enabled_sql}=FALSE)) S
            ON T.ID_COMPANY=S.ID_COMPANY
            WHEN MATCHED THEN UPDATE SET IS_ENABLED={enabled_sql}, UPDATED_AT=CURRENT_TIMESTAMP()
            WHEN NOT MATCHED THEN INSERT (ID_COMPANY,IS_ENABLED,CREATED_AT,UPDATED_AT)
                VALUES (S.ID_COMPANY,{enabled_sql},CURRENT_TIMESTAMP(),CURRENT_TIMESTAMP());
            {sync_sql('a.ID_COMPANY=@company')}
            COMMIT TRANSACTION;''',
            {'company':company_id})
        saved = get_mention_watch_config(company_id)
        if saved['is_enabled'] != is_enabled or (is_enabled and not saved['is_active']):
            raise HTTPException(409,'La société a changé pendant la sauvegarde ; actualisez la liste')
        return saved


def list_mention_watch_companies():
    """Only this active/eligible set will be available to the future scheduler."""
    rows = query_bq(f'''SELECT c.ID_COMPANY, c.NAME FROM `{COMPANY}` c
        INNER JOIN `{CONFIG}` m ON m.ID_COMPANY=c.ID_COMPANY AND m.IS_ENABLED=TRUE
        WHERE c.IS_ACTIVE=TRUE ORDER BY UPPER(c.NAME), c.ID_COMPANY''')
    return [{'id_company':r['ID_COMPANY'],'name':r['NAME']} for r in rows]


def require_mention_watch_enabled(company_id):
    config = get_mention_watch_config(company_id)
    if not config['is_active']:
        raise HTTPException(409,'La société est inactive')
    if not config['is_enabled']:
        raise HTTPException(409,'Veille Mentions désactivée pour cette société. Activez-la dans Companies avant de lancer une collecte.')
    return config
