"""Selected Corpo discovery -> Library, one resumable extraction segment per call."""
from __future__ import annotations

import json
from fastapi import HTTPException
from core.company import watch_discovery_service as discovery
from core.library import company_watch_library as library
from utils.gcs import bucket, BUCKET_NAME


def _original(uri):
    prefix = f"gs://{BUCKET_NAME}/"
    if not uri.startswith(prefix):
        raise ValueError("Emplacement de capture inattendu")
    return bucket.blob(uri[len(prefix):]).download_as_bytes()


def _state(candidate_id, status, document_id=None, error=None):
    discovery._query(f"""UPDATE `{discovery.DISCOVERY}` SET LIBRARY_STATUS=@status,
        ID_DOCUMENT=COALESCE(@document, ID_DOCUMENT), ERROR=@error, UPDATED_AT=CURRENT_TIMESTAMP()
        WHERE ID_DISCOVERY=@id""", [discovery._p('status','STRING',status),
        discovery._p('document','STRING',document_id), discovery._p('error','STRING',error),
        discovery._p('id','STRING',candidate_id)])


def import_step(candidate_id):
    with library.document_lock('library-import-' + candidate_id):
        candidate = discovery.get_candidate(candidate_id)
        if candidate['STATUS'] == 'DISMISSED':
            raise HTTPException(409, "Cette publication est ignorée ; restaurez-la avant de l'importer")
        watch = discovery.active_watch(candidate['ID_COMPANY'], candidate['ID_COMPANY_WATCH'])
        document_id = candidate.get('ID_DOCUMENT')
        if candidate.get('LIBRARY_STATUS') == 'IMPORTED' and document_id:
            doc = library.get_document(watch['id_company'], watch['id_company_watch'], document_id)
            if doc.get('EXTRACTION_STATUS') == 'COMPLETE':
                return {**library.response_document(doc, True), 'library_status':'IMPORTED'}
        # Atomic claim prevents a concurrent dismiss from racing the import.
        claimed = discovery._query(f"""UPDATE `{discovery.DISCOVERY}`
            SET LIBRARY_STATUS='IMPORTING', ERROR=NULL, UPDATED_AT=CURRENT_TIMESTAMP()
            WHERE ID_DISCOVERY=@id AND STATUS != 'DISMISSED';
            SELECT @@row_count AS UPDATED_COUNT;""", [discovery._p('id','STRING',candidate_id)])
        if not claimed or int(claimed[0]['UPDATED_COUNT']) != 1:
            raise HTTPException(409, "La publication a changé de statut ; actualisez la liste")
        try:
            if not document_id:
                # Capture only if absent. The stock is an internal technical operation.
                if not candidate.get('SNAPSHOT_URI'):
                    discovery.store_candidate(candidate_id)
                    candidate = discovery.get_candidate(candidate_id)
                metadata = json.loads(library._read_uri(candidate['SNAPSHOT_URI']))
                text = library._read_uri(metadata['text_storage_uri'])
                frozen_watch = {**watch, 'source_role': metadata.get('source_role', watch['source_role']),
                    'author_name': metadata.get('author_name') or metadata.get('author_id')}
                if metadata.get('provider') == 'BRIGHTDATA':
                    frozen_watch['source_type'] = 'LINKEDIN'
                result = library.register_publication(frozen_watch, source_url=metadata['url'],
                    original=_original(metadata['storage_uri']), text=text, title=metadata['title'],
                    mime='application/json' if metadata.get('provider') == 'BRIGHTDATA' else 'text/html',
                    published_at=metadata.get('published_at'), date_precision=metadata.get('date_precision','UNKNOWN'),
                    author=frozen_watch['author_name'],
                    extra={**metadata, 'id_discovery':candidate_id, 'id_stock':candidate.get('ID_STOCK'),
                           'capture_metadata_uri':candidate['SNAPSHOT_URI']})
                document_id = result['id_document']
            # Link before calling the LLM: retries reuse both the document and its cursor.
            _state(candidate_id, 'IMPORTING', document_id)
            result = library.extract_step(watch['id_company'], watch['id_company_watch'], document_id)
            status = 'IMPORTED' if result['status'] == 'COMPLETE' else 'IMPORTING'
            _state(candidate_id, status, document_id)
            return {**result, 'library_status': status}
        except HTTPException as exc:
            if exc.status_code != 409:
                _state(candidate_id,'ERROR',document_id,str(exc.detail)[:2000])
            raise
        except Exception as exc:
            _state(candidate_id,'ERROR',document_id,str(exc)[:2000])
            raise


def list_corpo_library(company_id=None, offset=0, limit=50):
    params = [library._p('limit','INT64',limit+1),library._p('offset','INT64',offset)]
    where = 'd.ID_COMPANY_WATCH IS NOT NULL'
    if company_id:
        where += ' AND d.ID_COMPANY=@company'
        params.append(library._p('company','STRING',company_id))
    rows = library._query(f"""SELECT d.ID_DOCUMENT, d.TITLE, d.SOURCE_URL, d.PUBLISHED_AT,
        d.COLLECTED_AT, d.AUTHOR_NAME, d.ID_COMPANY, d.ID_COMPANY_WATCH, d.DOCUMENT_TYPE,
        d.EXTRACTION_STATUS, d.EXTRACTION_ERROR, d.NEXT_CHUNK, d.CHUNK_COUNT,
        c.NAME AS COMPANY_NAME, w.LABEL AS WATCH_LABEL,
        (SELECT COUNT(*) FROM `{library.UNIT}` u WHERE u.ID_DOCUMENT=d.ID_DOCUMENT) AS UNIT_COUNT
        FROM `{library.DOCUMENT}` d
        LEFT JOIN `{discovery.COMPANY}` c ON c.ID_COMPANY=d.ID_COMPANY
        LEFT JOIN `{discovery.WATCH}` w ON w.ID_COMPANY_WATCH=d.ID_COMPANY_WATCH AND w.ID_COMPANY=d.ID_COMPANY
        WHERE {where} ORDER BY COALESCE(d.PUBLISHED_AT,d.COLLECTED_AT,d.CREATED_AT) DESC, d.ID_DOCUMENT
        LIMIT @limit OFFSET @offset""", params)
    return {'items':[{k.lower():v for k,v in dict(r).items()} for r in rows[:limit]],
            'has_more':len(rows)>limit}


def corpo_library_detail(document_id, offset=0, limit=100):
    rows=library._query(f"SELECT * FROM `{library.DOCUMENT}` WHERE ID_DOCUMENT=@id AND ID_COMPANY_WATCH IS NOT NULL LIMIT 1",
        [library._p('id','STRING',document_id)])
    if not rows:
        raise HTTPException(404,'Publication Library Corpo introuvable')
    doc=dict(rows[0])
    detail=library.publication_detail(doc['ID_COMPANY'],doc['ID_COMPANY_WATCH'],document_id,offset,limit)
    metadata=json.loads(library._read_uri(doc['METADATA_STORAGE_URI']))
    extra=metadata.get('extra') or {}
    return {**detail,'published_at':doc.get('PUBLISHED_AT'),'author_name':doc.get('AUTHOR_NAME'),
        'id_company':doc['ID_COMPANY'],'id_company_watch':doc['ID_COMPANY_WATCH'],
        'monitored_account_url':extra.get('monitored_account_url'), 'author_id':extra.get('author_id'),
        'repost':extra.get('repost'), 'share_date':extra.get('share_date'),
        'offset':offset,'limit':limit}
