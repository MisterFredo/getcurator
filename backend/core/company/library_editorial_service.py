"""Reversible editorial withdrawal of a Mention or LinkedIn post, scoped to company + source URL."""
import hashlib
import json
import uuid
from fastapi import HTTPException
from core.library import company_watch_library as lib
from core.company.watch_http import url_key
EVENT=f'{lib.BASE}.RATECARD_LIBRARY_EDITORIAL_EVENT'

def set_mention_editorial(document_id,is_withdrawn,reason=None):
    status='WITHDRAWN' if is_withdrawn else 'ACTIVE'
    # Same lock as mention imports: rejection and import cannot commit together.
    scope=hashlib.sha256(json.dumps(lib.BASE,sort_keys=True,ensure_ascii=False).encode()).hexdigest()
    with lib.document_lock('mention-batch-'+scope):
        rows=lib._query(f'SELECT ID_COMPANY,SOURCE_URL,DOCUMENT_TYPE,ID_COMPANY_WATCH FROM `{lib.DOCUMENT}` WHERE ID_DOCUMENT=@id LIMIT 1',[lib._p('id','STRING',document_id)])
        if not rows:raise HTTPException(404,'Mention introuvable')
        doc=dict(rows[0])
        kind = doc.get('DOCUMENT_TYPE')
        if kind != 'MENTION' and (kind != 'LINKEDIN' or not doc.get('ID_COMPANY_WATCH')):
            raise HTTPException(409, 'Ce retrait concerne les mentions et les publications LinkedIn de Veille')
        kind_param = lib._p('kind', 'STRING', kind)
        key=url_key(doc['SOURCE_URL'])
        versions=lib._query(f"SELECT ID_DOCUMENT,SOURCE_URL FROM `{lib.DOCUMENT}` WHERE ID_COMPANY=@company AND DOCUMENT_TYPE=@kind",[lib._p('company','STRING',doc['ID_COMPANY']), kind_param])
        ids={document_id}
        for version in versions:
            try:
                if version.get('SOURCE_URL') and url_key(version['SOURCE_URL'])==key:ids.add(version['ID_DOCUMENT'])
            except (ValueError,TypeError):continue
        from google.cloud import bigquery
        params=[kind_param,lib._p('id','STRING',document_id),lib._p('company','STRING',doc['ID_COMPANY']),
            lib._p('url','STRING',doc['SOURCE_URL']),lib._p('key','STRING',key),
            lib._p('status','STRING',status),lib._p('reason','STRING',(reason or '').strip()[:1000] or None),
            lib._p('event','STRING',str(uuid.uuid4())),bigquery.ArrayQueryParameter('ids','STRING',sorted(ids))]
        result=lib._query(f"""DECLARE changed INT64 DEFAULT 0;
        BEGIN TRANSACTION;
        UPDATE `{lib.DOCUMENT}`
          SET EDITORIAL_STATUS=@status, EDITORIAL_UPDATED_AT=CURRENT_TIMESTAMP(),
              EDITORIAL_REASON=@reason, EDITORIAL_URL_KEY=@key
          WHERE ID_COMPANY=@company AND DOCUMENT_TYPE=@kind
            AND (ID_DOCUMENT IN UNNEST(@ids) OR EDITORIAL_URL_KEY=@key)
            AND COALESCE(EDITORIAL_STATUS,'ACTIVE') != @status;
        SET changed=@@row_count;
        IF changed>0 THEN
          INSERT INTO `{EVENT}` (ID_EVENT,ID_DOCUMENT,ID_COMPANY,SOURCE_URL,URL_KEY,EDITORIAL_STATUS,REASON,CREATED_AT)
          VALUES (@event,@id,@company,@url,@key,@status,@reason,CURRENT_TIMESTAMP());
        END IF;
        COMMIT TRANSACTION;
        SELECT changed AS CHANGED;""",params)
    return {'status':'ok','id_document':document_id,'editorial_status':status,
            'changed':int(result[0]['CHANGED']) if result else 0}
