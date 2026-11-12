"""Import LinkedIn captures by batch using their existing immutable storage objects."""

import hashlib
import json
import logging
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone

from google.cloud import bigquery

from core.company import watch_discovery_service as discovery
from core.library import company_watch_library as library
from utils.gcs import BUCKET_NAME, bucket

logger = logging.getLogger(__name__)
WORKERS = 4


def _capture_blob(uri):
    prefix = f"gs://{BUCKET_NAME}/"
    if not isinstance(uri, str) or not uri.startswith(prefix + "company-watch/brightdata/captures/"):
        raise ValueError("Emplacement de capture LinkedIn inattendu")
    return bucket.blob(uri[len(prefix):])


def _prepare(row):
    snapshot = row["SNAPSHOT_URI"]
    _capture_blob(snapshot)
    capture = json.loads(library._read_uri(snapshot))
    if capture.get("provider") != "BRIGHTDATA" or capture["url"] != row["URL"]:
        raise ValueError("Provenance ou URL de capture inattendue")
    for key in ("id_company", "id_company_watch"):
        if capture.get(key) != row[key.upper()]:
            raise ValueError("Rattachement de capture inattendu")

    text_uri = capture["text_storage_uri"]
    _capture_blob(text_uri)
    text = library._read_uri(text_uri)
    if not text.strip():
        raise ValueError("Publication sans texte")
    content_hash = hashlib.sha256(text.encode("utf-8")).hexdigest()
    if content_hash != capture["content_sha256"]:
        raise ValueError("Empreinte du texte de capture invalide")

    original_uri = capture["storage_uri"]
    original = _capture_blob(original_uri)
    original.reload()
    original_hash = capture["original_sha256"]
    identity = json.dumps(
        [row["ID_COMPANY_WATCH"], capture["url"], content_hash, library.VERSION],
        ensure_ascii=False,
    )
    document_id = str(uuid.uuid5(uuid.NAMESPACE_URL, identity))
    author = capture.get("author_name") or capture.get("author_id") or row["WATCH_AUTHOR"]
    chunks = library.split_text(text)
    meta = {
        "company_name": row["COMPANY_NAME"],
        "source_url": capture["url"],
        "author_name": author,
        "source_role": row["SOURCE_ROLE"],
        "collected_at": capture.get("captured_at") or datetime.now(timezone.utc).isoformat(),
        "chunks": chunks,
        "extraction_version": library.VERSION,
        "extra": {**capture, "id_discovery": row["ID_DISCOVERY"],
                  "id_stock": row["ID_STOCK"], "capture_metadata_uri": snapshot},
    }
    # Only the Library-specific metadata is written. Its location is keyed by
    # the discovery and snapshot, so a concurrent standard import has its own path.
    capture_key = hashlib.sha256(f"{row['ID_DISCOVERY']}:{snapshot}".encode("utf-8")).hexdigest()
    meta_uri = library._upload(
        f"company-watch/documents/{document_id}/capture-{capture_key}.json",
        json.dumps(meta, ensure_ascii=False).encode("utf-8"),
        "application/json",
    )
    return {
        "candidate": row["ID_DISCOVERY"], "document": document_id, "snapshot": snapshot,
        "source_role": row["SOURCE_ROLE"],
        "url": capture["url"], "title": capture["title"], "author": author,
        "sha": original_hash, "original": original_uri, "size": original.size,
        "text": text_uri, "metadata": meta_uri, "hash": content_hash,
        "chunks": len(chunks), "published": capture.get("published_at"),
        "precision": capture.get("date_precision") or "UNKNOWN",
        "captured": meta["collected_at"],
    }


def _commit(prepared):
    if not prepared:
        return []
    return library._query(f"""
        BEGIN TRANSACTION;
        CREATE TEMP TABLE linked AS
        WITH payload AS (
            SELECT JSON_VALUE(j, '$.candidate') AS candidate,
                   JSON_VALUE(j, '$.document') AS document, j
            FROM UNNEST(JSON_QUERY_ARRAY(@payload)) j
        ), eligible AS (
            SELECT p.*, d.ID_COMPANY, d.ID_COMPANY_WATCH, d.ID_DOCUMENT AS previous_document,
                   d.URL AS source_url
            FROM payload p
            JOIN `{discovery.DISCOVERY}` d ON d.ID_DISCOVERY=p.candidate
            JOIN `{discovery.WATCH}` w
              ON w.ID_COMPANY_WATCH=d.ID_COMPANY_WATCH AND w.ID_COMPANY=d.ID_COMPANY
            JOIN `{library.BASE}.RATECARD_COMPANY` c ON c.ID_COMPANY=d.ID_COMPANY
            WHERE d.SNAPSHOT_URI=JSON_VALUE(p.j, '$.snapshot')
              AND d.URL=JSON_VALUE(p.j, '$.url')
              AND w.IS_ACTIVE=TRUE AND c.IS_ACTIVE=TRUE
              AND w.SOURCE_TYPE='LINKEDIN'
              AND IF(w.SOURCE_ROLE='EMPLOYEE' OR w.ID_CONTACT IS NOT NULL, 'EMPLOYEE', 'CORPORATE')
                  = JSON_VALUE(p.j, '$.source_role')
              AND d.STATUS IN ('NEW', 'STORED')
              AND COALESCE(d.LIBRARY_STATUS, 'PENDING') != 'IMPORTED'
              AND (COALESCE(d.LIBRARY_STATUS, 'PENDING') != 'IMPORTING'
                   OR d.UPDATED_AT < TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 15 MINUTE))
        ), withdrawn AS (
            SELECT d.ID_COMPANY, d.SOURCE_URL, MIN(d.ID_DOCUMENT) AS document
            FROM `{library.DOCUMENT}` d
            JOIN (SELECT DISTINCT ID_COMPANY, source_url FROM eligible) e
              ON d.ID_COMPANY=e.ID_COMPANY AND d.SOURCE_URL=e.source_url
            WHERE d.DOCUMENT_TYPE='LINKEDIN' AND d.EDITORIAL_STATUS='WITHDRAWN'
            GROUP BY d.ID_COMPANY, d.SOURCE_URL
        )
        SELECT e.*, COALESCE(w.document, old.ID_DOCUMENT, e.document) AS target_document,
               w.document IS NOT NULL OR COALESCE(old.EDITORIAL_STATUS, 'ACTIVE')='WITHDRAWN' AS withdrawn
        FROM eligible e
        LEFT JOIN withdrawn w ON w.ID_COMPANY=e.ID_COMPANY AND w.SOURCE_URL=e.source_url
        LEFT JOIN `{library.DOCUMENT}` old ON old.ID_DOCUMENT=e.previous_document
             AND old.ID_COMPANY=e.ID_COMPANY AND old.ID_COMPANY_WATCH=e.ID_COMPANY_WATCH
             AND old.SOURCE_URL=e.source_url;

        MERGE `{library.DOCUMENT}` d
        USING (
            SELECT * FROM linked WHERE NOT withdrawn
            QUALIFY ROW_NUMBER() OVER (PARTITION BY target_document ORDER BY candidate)=1
        ) s ON d.ID_DOCUMENT=s.target_document
        WHEN NOT MATCHED THEN INSERT (
            ID_DOCUMENT, ID_SOURCE, TITLE, ORIGINAL_FILENAME, SHA256, STORAGE_URI, FILE_SIZE_BYTES,
            SOURCE_URL, DOCUMENT_TYPE, ID_COMPANY, ID_COMPANY_WATCH, AUTHOR_NAME, SOURCE_ROLE,
            COLLECTED_AT, LAST_SEEN_AT, PUBLISHED_AT, PUBLICATION_DATE_PRECISION, TEXT_STORAGE_URI,
            METADATA_STORAGE_URI, CONTENT_SHA256, EXTRACTION_STATUS, EXTRACTION_VERSION,
            NEXT_CHUNK, CHUNK_COUNT, CREATED_AT, UPDATED_AT
        ) VALUES (
            s.target_document, NULL, JSON_VALUE(s.j, '$.title'), 'original.json',
            JSON_VALUE(s.j, '$.sha'), JSON_VALUE(s.j, '$.original'),
            CAST(JSON_VALUE(s.j, '$.size') AS INT64), s.source_url, 'LINKEDIN',
            s.ID_COMPANY, s.ID_COMPANY_WATCH, JSON_VALUE(s.j, '$.author'), JSON_VALUE(s.j, '$.source_role'),
            COALESCE(SAFE_CAST(JSON_VALUE(s.j, '$.captured') AS TIMESTAMP), CURRENT_TIMESTAMP()),
            CURRENT_TIMESTAMP(), SAFE_CAST(JSON_VALUE(s.j, '$.published') AS TIMESTAMP),
            JSON_VALUE(s.j, '$.precision'), JSON_VALUE(s.j, '$.text'), JSON_VALUE(s.j, '$.metadata'),
            JSON_VALUE(s.j, '$.hash'), 'PENDING', @version, 0,
            CAST(JSON_VALUE(s.j, '$.chunks') AS INT64), CURRENT_TIMESTAMP(), CURRENT_TIMESTAMP()
        );

        UPDATE `{discovery.DISCOVERY}` d
        SET LIBRARY_STATUS='IMPORTED', ID_DOCUMENT=s.target_document,
            ERROR=NULL, UPDATED_AT=CURRENT_TIMESTAMP()
        FROM linked s WHERE d.ID_DISCOVERY=s.candidate;
        COMMIT TRANSACTION;

        SELECT candidate, withdrawn, target_document FROM linked;
    """, [
        library._p("payload", "STRING", json.dumps(prepared, ensure_ascii=False)),
        library._p("version", "STRING", library.VERSION),
    ])


def register_batch(*, limit, excluded_ids):
    rows = discovery._query(f"""
        SELECT DISTINCT d.ID_DISCOVERY, d.ID_COMPANY, d.ID_COMPANY_WATCH, d.ID_STOCK,
               d.URL, d.SNAPSHOT_URI, c.NAME AS COMPANY_NAME, w.AUTHOR_NAME AS WATCH_AUTHOR,
               IF(w.SOURCE_ROLE='EMPLOYEE' OR w.ID_CONTACT IS NOT NULL, 'EMPLOYEE', 'CORPORATE') AS SOURCE_ROLE
        FROM `{discovery.DISCOVERY}` d
        JOIN `{discovery.WATCH}` w
          ON w.ID_COMPANY_WATCH=d.ID_COMPANY_WATCH AND w.ID_COMPANY=d.ID_COMPANY
        JOIN `{library.BASE}.RATECARD_COMPANY` c ON c.ID_COMPANY=d.ID_COMPANY
        WHERE w.SOURCE_TYPE='LINKEDIN' AND w.IS_ACTIVE=TRUE AND c.IS_ACTIVE=TRUE
          AND d.STATUS IN ('NEW', 'STORED') AND d.SNAPSHOT_URI IS NOT NULL
          AND COALESCE(d.LIBRARY_STATUS, 'PENDING') != 'IMPORTED'
          AND (COALESCE(d.LIBRARY_STATUS, 'PENDING') != 'IMPORTING'
               OR d.UPDATED_AT < TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 15 MINUTE))
          AND d.ID_DISCOVERY NOT IN UNNEST(@excluded)
        ORDER BY d.ID_DISCOVERY
        LIMIT @limit
    """, [
        bigquery.ArrayQueryParameter("excluded", "STRING", list(excluded_ids)),
        library._p("limit", "INT64", limit),
    ])
    prepared, failures = [], []
    with ThreadPoolExecutor(max_workers=WORKERS) as pool:
        futures = [(row["ID_DISCOVERY"], pool.submit(_prepare, row)) for row in rows]
        for candidate_id, future in futures:
            try:
                prepared.append(future.result())
            except Exception:
                failures.append(candidate_id)
                logger.exception("Capture non préparée : %s", candidate_id)

    committed = _commit(prepared)
    if committed:
        from core.company.library_post_media import index_arrivals

        index_arrivals(sorted({row["target_document"] for row in committed if not row["withdrawn"]}))
    confirmed = {row["candidate"] for row in committed}
    failures.extend(item["candidate"] for item in prepared if item["candidate"] not in confirmed)
    withdrawn = sum(row["withdrawn"] for row in committed)
    return {
        "registered": len(committed) - withdrawn,
        "withdrawn": withdrawn,
        "failed": len(failures),
        "failed_ids": failures,
    }
