"""Selected Corpo discovery -> Library, one resumable extraction segment per call."""
from __future__ import annotations

import json
import logging
from datetime import date, timedelta
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


def import_step(candidate_id, *, register_only=False, qualify_on_arrival=True):
    with library.document_lock('library-import-' + candidate_id):
        candidate = discovery.get_candidate(candidate_id)
        if candidate['STATUS'] == 'DISMISSED':
            raise HTTPException(409, "Cette publication est ignorée ; restaurez-la avant de l'importer")
        watch = discovery.active_watch(candidate['ID_COMPANY'], candidate['ID_COMPANY_WATCH'])
        document_id = candidate.get('ID_DOCUMENT')
        if candidate.get('LIBRARY_STATUS') == 'IMPORTED' and document_id:
            doc = library.get_document(watch['id_company'], watch['id_company_watch'], document_id)
            if register_only or doc.get('EXTRACTION_STATUS') == 'COMPLETE':
                return {**library.response_document(doc, True), 'library_status':'IMPORTED'}
        if register_only and not document_id:
            withdrawn = library._query(f"""
                SELECT ID_DOCUMENT FROM `{library.DOCUMENT}`
                WHERE ID_COMPANY=@company AND SOURCE_URL=@url
                  AND DOCUMENT_TYPE='LINKEDIN' AND EDITORIAL_STATUS='WITHDRAWN'
                ORDER BY ID_DOCUMENT LIMIT 1
            """, [library._p('company', 'STRING', candidate['ID_COMPANY']),
                   library._p('url', 'STRING', candidate['URL'])])
            if withdrawn:
                _state(candidate_id, 'IMPORTED', withdrawn[0]['ID_DOCUMENT'])
                return {'id_document': withdrawn[0]['ID_DOCUMENT'],
                        'library_status': 'IMPORTED', 'withdrawn': True}
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
                    author=frozen_watch['author_name'], qualify_on_arrival=qualify_on_arrival,
                    extra={**metadata, 'id_discovery':candidate_id, 'id_stock':candidate.get('ID_STOCK'),
                           'capture_metadata_uri':candidate['SNAPSHOT_URI']})
                document_id = result['id_document']
                if metadata.get('provider') == 'BRIGHTDATA':
                    from core.company.library_post_media import index_arrivals

                    index_arrivals([document_id])
            if register_only:
                _state(candidate_id, 'IMPORTED', document_id)
                return {'id_document': document_id, 'library_status': 'IMPORTED'}
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


def register_employee_backlog(watch_id=None, *, limit=None, excluded_ids=(), qualify_on_arrival=True):
    """Register captured employee posts, including previous collections."""
    return _register_linkedin_backlog(
        watch_id, employees_only=True, limit=limit, excluded_ids=excluded_ids,
        qualify_on_arrival=qualify_on_arrival,
    )


def register_corporate_posts(watch_id):
    return _register_linkedin_backlog(watch_id, employees_only=False)


def _register_linkedin_backlog(watch_id, *, employees_only, limit=None,
                               excluded_ids=(), qualify_on_arrival=True):
    role_filter = ("w.SOURCE_ROLE='EMPLOYEE' OR w.ID_CONTACT IS NOT NULL" if employees_only
                   else "COALESCE(w.SOURCE_ROLE, 'CORPORATE')='CORPORATE' AND w.ID_CONTACT IS NULL")
    params = []
    scope = ""
    if watch_id is not None:
        scope = "AND d.ID_COMPANY_WATCH=@watch"
        params.append(discovery._p('watch', 'STRING', watch_id))
    if excluded_ids:
        from google.cloud import bigquery

        scope += " AND d.ID_DISCOVERY NOT IN UNNEST(@excluded)"
        params.append(bigquery.ArrayQueryParameter('excluded', 'STRING', list(excluded_ids)))
    limit_clause = ""
    if limit is not None:
        limit_clause = "LIMIT @limit"
        params.append(discovery._p('limit', 'INT64', limit))
    rows = discovery._query(f"""
        SELECT DISTINCT d.ID_DISCOVERY
        FROM `{discovery.DISCOVERY}` d
        JOIN `{discovery.WATCH}` w USING (ID_COMPANY_WATCH)
        WHERE ({role_filter})
          AND w.SOURCE_TYPE='LINKEDIN'
          AND w.IS_ACTIVE=TRUE
          AND d.STATUS IN ('NEW', 'STORED')
          AND d.SNAPSHOT_URI IS NOT NULL
          AND COALESCE(d.LIBRARY_STATUS, 'PENDING') != 'IMPORTED'
          {scope}
        ORDER BY d.ID_DISCOVERY
        {limit_clause}
    """, params)
    result = {'registered': 0, 'withdrawn': 0, 'failed': 0, 'failed_ids': []}
    for row in rows:
        candidate_id = row['ID_DISCOVERY']
        try:
            outcome = import_step(candidate_id, register_only=True, qualify_on_arrival=qualify_on_arrival)
        except Exception:
            result['failed'] += 1
            result['failed_ids'].append(candidate_id)
            logging.getLogger(__name__).exception(
                "LinkedIn Library registration failed for %s", candidate_id
            )
        else:
            result['withdrawn' if outcome.get('withdrawn') else 'registered'] += 1
    return result


def list_corpo_library(company_id=None, offset=0, limit=50, query=None,
                       sort="published_at", direction="desc", status=None,
                       published_from=None, published_to=None, document_type=None, editorial_status="ACTIVE",
                       with_summary=False, qualification=None, post_type=None, review_state=None, origin=None, media_format=None):
    from core.company.library_post_funnel import POST_TYPES, TABLE, VERSION
    from core.company.library_post_media import TABLE as MEDIA_TABLE

    from core.company.library_post_review import EMPLOYEE_ROLE, LATEST

    if origin not in {None, "", "CORPORATE", "EMPLOYEE"}:
        raise ValueError("Origine invalide")

    review_filters = {
        "TO_REVIEW": "d.QUALIFICATION_ROLE IS NOT NULL AND d.QUALIFICATION_VERDICT IS NOT NULL AND d.REVIEW_ID IS NULL",
        "REVIEWED": "d.REVIEW_ID IS NOT NULL",
    }
    if review_state and review_state not in review_filters:
        raise ValueError("État de revue invalide")
    qualification_filters = {
        "GO": "d.QUALIFICATION_ROLE='EMPLOYEE' AND d.QUALIFICATION_VERDICT IN ('SIGNAL_SOCIETE','PRISE_DE_PAROLE_METIER')",
        "NO_GO": "d.QUALIFICATION_ROLE='EMPLOYEE' AND d.QUALIFICATION_VERDICT='BRUIT'",
        "REVIEW": "d.QUALIFICATION_ROLE='EMPLOYEE' AND d.QUALIFICATION_VERDICT='A_VERIFIER'",
        "PENDING": "d.QUALIFICATION_ROLE IS NOT NULL AND d.QUALIFICATION_VERDICT IS NULL",
    }
    if qualification and qualification not in qualification_filters:
        raise ValueError("Filtre de qualification invalide")
    if post_type and post_type not in POST_TYPES:
        raise ValueError("Type principal invalide")
    if not 1 <= limit <= 200 or offset < 0:
        raise ValueError("Pagination invalide")
    sorts = {"published_at":"d.PUBLISHED_AT", "imported_at":"d.CREATED_AT",
             "company":"LOWER(COALESCE(c.NAME,''))", "title":"LOWER(COALESCE(d.TITLE,''))",
             "units":"UNIT_COUNT"}
    if sort not in sorts or direction not in {"asc","desc"}:
        raise ValueError("Tri invalide")
    if status not in {None,"", "COMPLETE", "PENDING", "ERROR"}:
        raise ValueError("État invalide")
    start = date.fromisoformat(published_from) if published_from else None
    end = date.fromisoformat(published_to) if published_to else None
    if start and end and start > end:
        raise ValueError("La date de début doit précéder la date de fin")
    params = [library._p('limit','INT64',limit+1),library._p('offset','INT64',offset)]
    where = ["(d.ID_COMPANY_WATCH IS NOT NULL OR d.DOCUMENT_TYPE='MENTION')"]
    if editorial_status not in {'ACTIVE','WITHDRAWN','ALL'}:raise ValueError('État éditorial invalide')
    if editorial_status != 'ALL':
        where.append("COALESCE(d.EDITORIAL_STATUS,'ACTIVE')=@editorial")
        params.append(library._p('editorial','STRING',editorial_status))
    if document_type:
        if document_type not in {'MENTION','CORPORATE'}:raise ValueError('Type invalide')
        where.append("d.DOCUMENT_TYPE='MENTION'" if document_type=='MENTION' else "d.ID_COMPANY_WATCH IS NOT NULL")
    # Summary scope ignores company/text/date/extraction filters. Company options
    # retain withdrawn-only companies, so restoration remains discoverable.
    if origin:
        where.append("d.QUALIFICATION_ROLE=@origin")
        params.append(library._p('origin','STRING',origin))
    global_predicate=' AND '.join(where)
    media_filters = {"DOCUMENT": "d.HAS_DOCUMENT", "VIDEO": "d.HAS_VIDEO",
                     "ANY": "(d.HAS_DOCUMENT OR d.HAS_VIDEO)"}
    if media_format:
        if media_format not in media_filters:
            raise ValueError("Format média invalide")
        where.append(media_filters[media_format])
    if company_id:
        where.append('d.ID_COMPANY=@company')
        params.append(library._p('company','STRING',company_id))
    if query and query.strip():
        query = query.strip()
        if len(query) > 500:
            raise ValueError("Recherche limitée à 500 caractères")
        # Literal case-insensitive substring, not SQL LIKE or user-controlled SQL.
        where.append("""(CONTAINS_SUBSTR(COALESCE(d.TITLE,''),@query)
            OR CONTAINS_SUBSTR(COALESCE(d.AUTHOR_NAME,''),@query)
            OR CONTAINS_SUBSTR(COALESCE(d.SOURCE_URL,''),@query)
            OR CONTAINS_SUBSTR(COALESCE(c.NAME,''),@query)
            OR CONTAINS_SUBSTR(COALESCE(w.LABEL,''),@query)
            OR EXISTS (SELECT 1 FROM `{units}` evidence WHERE evidence.ID_DOCUMENT=d.ID_DOCUMENT
                AND (CONTAINS_SUBSTR(COALESCE(evidence.FACT,''),@query)
                     OR CONTAINS_SUBSTR(COALESCE(evidence.QUOTE,''),@query))))""".format(units=library.UNIT))
        params.append(library._p('query','STRING',query))
    if status:
        where.append('d.EXTRACTION_STATUS=@status'); params.append(library._p('status','STRING',status))
    if start:
        where.append("d.PUBLISHED_AT >= TIMESTAMP(@start,'Europe/Paris')")
        params.append(library._p('start','DATE',start))
    if end:
        where.append("d.PUBLISHED_AT < TIMESTAMP(@end,'Europe/Paris')")
        params.append(library._p('end','DATE',end+timedelta(days=1)))
    predicate = ' AND '.join(where)
    scoped = predicate.replace('c.NAME','d.COMPANY_NAME').replace('w.LABEL','d.WATCH_LABEL')
    selection = []
    if qualification:
        selection.append(qualification_filters[qualification])
    if post_type:
        selection.append('d.QUALIFICATION_TYPE=@post_type')
        params.append(library._p('post_type','STRING',post_type))
    if review_state:
        selection.append(review_filters[review_state])
    selection = ' AND '.join(selection) or 'TRUE'
    params.append(library._p('qualification_version','STRING',VERSION))

    ordering = sorts[sort] + ' ' + direction.upper() + ' NULLS LAST, d.ID_DOCUMENT ASC'
    base_sql=f"""SELECT d.ID_DOCUMENT, d.TITLE, d.SOURCE_URL, d.PUBLISHED_AT,
        d.CREATED_AT AS IMPORTED_AT, d.COLLECTED_AT, d.AUTHOR_NAME, d.ID_COMPANY, d.ID_COMPANY_WATCH, d.DOCUMENT_TYPE,
        d.EDITORIAL_STATUS, d.EDITORIAL_UPDATED_AT, d.EDITORIAL_REASON,
        d.EXTRACTION_STATUS, d.EXTRACTION_ERROR, d.NEXT_CHUNK, d.CHUNK_COUNT,
        c.NAME AS COMPANY_NAME, w.LABEL AS WATCH_LABEL,
        CASE WHEN d.DOCUMENT_TYPE='LINKEDIN' AND d.ID_COMPANY_WATCH IS NOT NULL THEN
          CASE WHEN {EMPLOYEE_ROLE}
               THEN 'EMPLOYEE' ELSE 'CORPORATE' END
        END AS QUALIFICATION_ROLE,
        COALESCE(r.VERDICT, v.VERDICT) AS QUALIFICATION_VERDICT,
        COALESCE(r.TYPE_PRINCIPAL, v.TYPE_PRINCIPAL) AS QUALIFICATION_TYPE,
        r.ID_REVIEW AS REVIEW_ID,
        COALESCE(m.HAS_VIDEO, FALSE) AS HAS_VIDEO,
        COALESCE(m.HAS_DOCUMENT, FALSE) AS HAS_DOCUMENT,
        m.DOCUMENT_PAGE_COUNT, m.VIDEO_DURATION,
        (SELECT COUNT(*) FROM `{library.UNIT}` u WHERE u.ID_DOCUMENT=d.ID_DOCUMENT) AS UNIT_COUNT
        FROM `{library.DOCUMENT}` d
        LEFT JOIN `{discovery.COMPANY}` c ON c.ID_COMPANY=d.ID_COMPANY
        LEFT JOIN `{discovery.WATCH}` w ON w.ID_COMPANY_WATCH=d.ID_COMPANY_WATCH AND w.ID_COMPANY=d.ID_COMPANY
        LEFT JOIN (
          SELECT ID_COMPANY, ID_DOCUMENT, VERDICT, TYPE_PRINCIPAL
          FROM `{TABLE}` WHERE VERSION=@qualification_version
          QUALIFY ROW_NUMBER() OVER (
            PARTITION BY ID_COMPANY, ID_DOCUMENT ORDER BY CREATED_AT DESC, VERDICT, TYPE_PRINCIPAL
          )=1
        ) v ON v.ID_COMPANY=d.ID_COMPANY AND v.ID_DOCUMENT=d.ID_DOCUMENT
           AND d.DOCUMENT_TYPE='LINKEDIN' AND d.ID_COMPANY_WATCH IS NOT NULL
        LEFT JOIN (
          SELECT ID_DOCUMENT, STORAGE_URI, LOGICAL_OR(HAS_VIDEO) AS HAS_VIDEO,
                 LOGICAL_OR(HAS_DOCUMENT) AS HAS_DOCUMENT,
                 MAX(DOCUMENT_PAGE_COUNT) AS DOCUMENT_PAGE_COUNT, MAX(VIDEO_DURATION) AS VIDEO_DURATION
          FROM `{MEDIA_TABLE}` GROUP BY ID_DOCUMENT, STORAGE_URI
        ) m ON d.DOCUMENT_TYPE='LINKEDIN' AND m.ID_DOCUMENT=d.ID_DOCUMENT
           AND m.STORAGE_URI=d.STORAGE_URI
        LEFT JOIN ({LATEST}) r ON r.ID_COMPANY=d.ID_COMPANY AND r.ID_DOCUMENT=d.ID_DOCUMENT
           AND d.DOCUMENT_TYPE='LINKEDIN' AND d.ID_COMPANY_WATCH IS NOT NULL
        WHERE (d.ID_COMPANY_WATCH IS NOT NULL OR d.DOCUMENT_TYPE='MENTION')"""
    if document_type:
        base_sql += " AND d.DOCUMENT_TYPE='MENTION'" if document_type=='MENTION' else " AND d.ID_COMPANY_WATCH IS NOT NULL"
    order=ordering.replace('c.NAME','d.COMPANY_NAME')
    company_origin = 'AND QUALIFICATION_ROLE=@origin' if origin else ''
    if with_summary:
        # One BigQuery request returns the page, exact counts and company options
        # from the same query snapshot. No per-company or per-row count queries.
        response=library._query(f"""WITH library_base AS ({base_sql}),
          scope AS (SELECT d.* FROM library_base d WHERE {scoped}),
          filtered AS (SELECT d.* FROM scope d WHERE {selection})
          SELECT
            ARRAY(SELECT AS STRUCT d.* FROM filtered d ORDER BY {order} LIMIT @limit OFFSET @offset) AS ITEMS,
            (SELECT COUNT(*) FROM filtered) AS TOTAL,
            ARRAY(SELECT AS STRUCT QUALIFICATION_ROLE AS role,
                    QUALIFICATION_VERDICT AS verdict, QUALIFICATION_TYPE AS post_type, COUNT(*) AS total
                  FROM scope WHERE QUALIFICATION_ROLE IS NOT NULL
                  GROUP BY role, verdict, post_type) AS QUALIFICATION_SUMMARY,
            (SELECT COUNT(*) FROM library_base d WHERE {global_predicate}) AS GLOBAL_TOTAL,
            ARRAY(SELECT AS STRUCT company.* FROM (
                    SELECT DISTINCT ID_COMPANY AS id_company, COALESCE(COMPANY_NAME,ID_COMPANY) AS name
                    FROM library_base WHERE ID_COMPANY IS NOT NULL {company_origin}
                  ) company ORDER BY company.name,company.id_company) AS COMPANIES""",params)
        result=dict(response[0]) if response else {'ITEMS':[],'TOTAL':0,'GLOBAL_TOTAL':0,'COMPANIES':[]}
        page=list(result['ITEMS'] or [])
        return {'items':[{k.lower():v for k,v in dict(row).items()} for row in page[:limit]],
                'has_more':len(page)>limit,'offset':offset,'limit':limit,
                'total':int(result['TOTAL']),'global_total':int(result['GLOBAL_TOTAL']),
                'qualification_summary':[dict(item) for item in (result.get('QUALIFICATION_SUMMARY') or [])],
                'companies':[dict(company) for company in (result['COMPANIES'] or [])]}
    rows=library._query(f"""WITH library_base AS ({base_sql})
        SELECT d.* FROM library_base d WHERE ({scoped}) AND ({selection})
        ORDER BY {order} LIMIT @limit OFFSET @offset""",params)
    return {'items':[{k.lower():v for k,v in dict(r).items()} for r in rows[:limit]],
            'has_more':len(rows)>limit, 'offset':offset, 'limit':limit}



def corpo_library_detail(document_id, offset=0, limit=100):
    from core.company.library_post_review import EMPLOYEE_ROLE, TABLE as REVIEW_TABLE

    rows=library._query(f"""SELECT d.*, CASE WHEN {EMPLOYEE_ROLE} THEN 'EMPLOYEE' ELSE 'CORPORATE' END AS QUALIFICATION_ROLE
        FROM `{library.DOCUMENT}` d LEFT JOIN `{discovery.WATCH}` w
            ON w.ID_COMPANY=d.ID_COMPANY AND w.ID_COMPANY_WATCH=d.ID_COMPANY_WATCH
        WHERE d.ID_DOCUMENT=@id AND (d.ID_COMPANY_WATCH IS NOT NULL OR d.DOCUMENT_TYPE='MENTION') LIMIT 1""",
        [library._p('id','STRING',document_id)])
    if not rows:
        raise HTTPException(404,'Publication Library Corpo introuvable')
    doc=dict(rows[0])
    if doc.get('DOCUMENT_TYPE') == 'MENTION':
        if offset < 0 or not 1 <= limit <= 500:raise ValueError('Pagination invalide')
        units=library._query(f"SELECT * FROM `{library.UNIT}` WHERE ID_DOCUMENT=@id ORDER BY UNIT_ID LIMIT @limit OFFSET @offset",
            [library._p('id','STRING',document_id),library._p('limit','INT64',limit+1),library._p('offset','INT64',offset)])
        return {**library.response_document(doc),'document_type':'MENTION','editorial_status':doc.get('EDITORIAL_STATUS') or 'ACTIVE','editorial_reason':doc.get('EDITORIAL_REASON'),'published_at':doc.get('PUBLISHED_AT'),
            'author_name':doc.get('AUTHOR_NAME'),'text':library._read_uri(doc['TEXT_STORAGE_URI']),
            'units':[{k.lower():v for k,v in dict(u).items()} for u in units[:limit]],'has_more':len(units)>limit,
            'warning':"VERIFIED valide la présence de la citation, pas la vérité du fait."}
    detail=library.publication_detail(doc['ID_COMPANY'],doc['ID_COMPANY_WATCH'],document_id,offset,limit)
    metadata=json.loads(library._read_uri(doc['METADATA_STORAGE_URI']))
    extra=metadata.get('extra') or {}
    qualification = {}
    if doc.get('DOCUMENT_TYPE') == 'LINKEDIN':
        from core.company.library_post_funnel import TABLE, VERSION

        verdicts = library._query(f"""
            SELECT VERDICT AS qualification_verdict, TYPE_PRINCIPAL AS qualification_type,
                   MOTIF AS qualification_motif
            FROM `{TABLE}`
            WHERE ID_COMPANY=@company AND ID_DOCUMENT=@id AND VERSION=@version
            ORDER BY CREATED_AT DESC, VERDICT, TYPE_PRINCIPAL LIMIT 1
        """, [library._p('company','STRING',doc['ID_COMPANY']),
               library._p('id','STRING',document_id), library._p('version','STRING',VERSION)])
        if verdicts:
            qualification = dict(verdicts[0])
            qualification.update({f"automatic_{key}": value for key, value in verdicts[0].items()})
        reviews = library._query(f"""
            SELECT ID_REVIEW AS review_id, VERDICT AS qualification_verdict,
                   TYPE_PRINCIPAL AS qualification_type, MOTIF AS qualification_motif
            FROM `{REVIEW_TABLE}` WHERE ID_COMPANY=@company AND ID_DOCUMENT=@id
            ORDER BY CREATED_AT DESC, ID_REVIEW DESC LIMIT 1
        """, [library._p('company','STRING',doc['ID_COMPANY']),
               library._p('id','STRING',document_id)])
        if reviews:
            qualification.update(dict(reviews[0]))
        qualification['qualification_role'] = doc['QUALIFICATION_ROLE']
    return {**detail,**qualification,'published_at':doc.get('PUBLISHED_AT'),
        'document_type':doc.get('DOCUMENT_TYPE'),
        'editorial_status':doc.get('EDITORIAL_STATUS') or 'ACTIVE',
        'editorial_reason':doc.get('EDITORIAL_REASON'),'author_name':doc.get('AUTHOR_NAME'),
        'id_company':doc['ID_COMPANY'],'id_company_watch':doc['ID_COMPANY_WATCH'],
        'monitored_account_url':extra.get('monitored_account_url'), 'author_id':extra.get('author_id'),
        'repost':extra.get('repost'), 'share_date':extra.get('share_date'),
        'offset':offset,'limit':limit}
