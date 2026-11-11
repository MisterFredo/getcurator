"""Corporate publications in the common documentary tables (no fake PDF pages)."""
from __future__ import annotations

import hashlib
import json
import logging
import uuid
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException
from google.cloud import bigquery
from google.api_core.exceptions import NotFound, PreconditionFailed

from config import BQ_PROJECT, BQ_DATASET
from utils.bigquery_utils import get_bigquery_client
from utils.gcs import bucket, BUCKET_NAME
from core.company.watch_evidence import VERSION, split_text, validate_candidates, extract_candidates, parse_candidates

BASE = f"{BQ_PROJECT}.{BQ_DATASET}"
DOCUMENT = f"{BASE}.RATECARD_SOURCE_DOCUMENT"
UNIT = f"{BASE}.RATECARD_DOCUMENT_UNIT"


def _p(name, kind, value):
    return bigquery.ScalarQueryParameter(name, kind, value)


def _query(sql, params=()):
    return list(get_bigquery_client().query(sql, job_config=bigquery.QueryJobConfig(
        query_parameters=list(params))).result())


@contextmanager
def document_lock(document_id: str):
    """Cross-worker GCS lease; generation preconditions prevent deleting another lease."""
    blob = bucket.blob(f"company-watch/locks/{document_id}.json")
    generation = None
    for _ in range(2):
        try:
            blob.upload_from_string(json.dumps({"expires": (datetime.now(timezone.utc) + timedelta(minutes=15)).isoformat()}),
                                    content_type="application/json", if_generation_match=0)
            generation = blob.generation
            break
        except PreconditionFailed:
            try:
                blob.reload()
                previous_generation = blob.generation
                previous = json.loads(blob.download_as_text(if_generation_match=previous_generation))
                if datetime.fromisoformat(previous["expires"]) > datetime.now(timezone.utc):
                    raise HTTPException(409, "Ce document est déjà en cours de traitement ; réessayer ensuite")
                blob.delete(if_generation_match=previous_generation)
            except (NotFound, PreconditionFailed):
                continue
    if generation is None:
        raise HTTPException(409, "Document occupé")
    try:
        yield
    finally:
        try:
            blob.delete(if_generation_match=generation)
        except (NotFound, PreconditionFailed):
            pass


def _upload(path: str, data: bytes, mime: str):
    blob = bucket.blob(path)
    try:
        blob.upload_from_string(data, content_type=mime, if_generation_match=0)
    except PreconditionFailed:
        pass
    return f"gs://{BUCKET_NAME}/{path}"


def _read_uri(uri: str) -> str:
    prefix = f"gs://{BUCKET_NAME}/"
    if not uri.startswith(prefix):
        raise ValueError("Emplacement de stockage inattendu")
    return bucket.blob(uri[len(prefix):]).download_as_text(encoding="utf-8")


def get_document(company_id: str, watch_id: str, document_id: str) -> dict:
    rows = _query(f"""SELECT * FROM `{DOCUMENT}` WHERE ID_DOCUMENT=@id
        AND ID_COMPANY=@company AND ID_COMPANY_WATCH=@watch LIMIT 1""",
        [_p("id", "STRING", document_id), _p("company", "STRING", company_id), _p("watch", "STRING", watch_id)])
    if not rows:
        raise HTTPException(404, "Publication introuvable pour ce point de collecte")
    return dict(rows[0])


def response_document(document: dict, already_exists=False) -> dict:
    return {"id_document": document["ID_DOCUMENT"], "title": document.get("TITLE"),
            "source_url": document.get("SOURCE_URL"), "status": document.get("EXTRACTION_STATUS"),
            "next_chunk": document.get("NEXT_CHUNK") or 0,
            "chunk_count": document.get("CHUNK_COUNT") or 0, "already_exists": already_exists}


def register_publication(watch: dict, *, source_url: str, original: bytes, text: str,
                         title: str, mime: str, published_at=None, date_precision="UNKNOWN",
                         author=None, extra=None, qualify_on_arrival=True) -> dict:
    if not text.strip():
        raise ValueError("Publication sans texte")
    chunks = split_text(text)
    # Empreinte du texte = pas de nouvelle version due à une bannière HTML dynamique.
    content_hash = hashlib.sha256(text.encode("utf-8")).hexdigest()
    identity = json.dumps([watch["id_company_watch"], source_url, content_hash, VERSION], ensure_ascii=False)
    document_id = str(uuid.uuid5(uuid.NAMESPACE_URL, identity))
    params = [_p("id", "STRING", document_id)]
    with document_lock(document_id):
        existing = _query(f"SELECT * FROM `{DOCUMENT}` WHERE ID_DOCUMENT=@id LIMIT 1", params)
        if existing:
            _query(f"UPDATE `{DOCUMENT}` SET LAST_SEEN_AT=CURRENT_TIMESTAMP() WHERE ID_DOCUMENT=@id", params)
            return response_document(dict(existing[0]), True)
        path = f"company-watch/documents/{document_id}"
        original_hash = hashlib.sha256(original).hexdigest()
        # Un retry peut recevoir un HTML différent pour le même texte extrait.
        # Nommer l'original par son hash garantit SHA256 == octets réellement stockés.
        extension = {"text/html": "html", "application/json": "json"}.get(mime, "txt")
        filename = f"original-{original_hash}.{extension}"
        original_uri = _upload(f"{path}/{filename}", original, mime)
        text_uri = _upload(f"{path}/text.txt", text.encode("utf-8"), "text/plain; charset=utf-8")
        metadata = {"company_name": watch.get("company_name"), "source_url": source_url,
                    "author_name": author or watch.get("author_name"), "source_role": watch.get("source_role"),
                    "collected_at": datetime.now(timezone.utc).isoformat(), "chunks": chunks,
                    "extraction_version": VERSION, "extra": extra or {}}
        metadata_uri = _upload(f"{path}/metadata.json", json.dumps(metadata, ensure_ascii=False).encode(), "application/json")
        values = {"id": document_id, "company": watch["id_company"], "watch": watch["id_company_watch"],
                  "title": title, "filename": filename, "sha": original_hash, "uri": original_uri,
                  "source_url": source_url, "type": watch["source_type"],
                  "author": metadata["author_name"], "role": watch["source_role"],
                  "published": published_at, "precision": date_precision, "text_uri": text_uri,
                  "metadata_uri": metadata_uri, "content_hash": content_hash, "version": VERSION}
        params = [_p(k, "STRING", v) for k, v in values.items()]
        params += [_p("size", "INT64", len(original)), _p("chunks", "INT64", len(chunks))]
        _query(f"""INSERT INTO `{DOCUMENT}` (
            ID_DOCUMENT, ID_SOURCE, TITLE, ORIGINAL_FILENAME, SHA256, STORAGE_URI, FILE_SIZE_BYTES,
            SOURCE_URL, DOCUMENT_TYPE, ID_COMPANY, ID_COMPANY_WATCH, AUTHOR_NAME, SOURCE_ROLE,
            COLLECTED_AT, LAST_SEEN_AT, PUBLISHED_AT, PUBLICATION_DATE_PRECISION, TEXT_STORAGE_URI,
            METADATA_STORAGE_URI, CONTENT_SHA256, EXTRACTION_STATUS, EXTRACTION_VERSION,
            NEXT_CHUNK, CHUNK_COUNT, CREATED_AT, UPDATED_AT)
            VALUES (@id, NULL, @title, @filename, @sha, @uri, @size, @source_url, @type, @company,
              @watch, @author, @role, CURRENT_TIMESTAMP(), CURRENT_TIMESTAMP(),
              SAFE_CAST(@published AS TIMESTAMP), @precision, @text_uri, @metadata_uri,
              @content_hash, 'PENDING', @version, 0, @chunks, CURRENT_TIMESTAMP(), CURRENT_TIMESTAMP())""", params)
        if qualify_on_arrival and watch.get("source_type") == "LINKEDIN":
            try:
                from core.company.library_post_worker import wake_post_worker

                wake_post_worker()
            except Exception:
                logging.getLogger(__name__).exception(
                    "Démarrage de la qualification impossible pour %s", document_id
                )
        return {"id_document": document_id, "title": title, "source_url": source_url,
                "status": "PENDING", "next_chunk": 0, "chunk_count": len(chunks), "already_exists": False}


def extract_step(company_id: str, watch_id: str, document_id: str) -> dict:
    with document_lock(document_id):
        document = get_document(company_id, watch_id, document_id)
        if document.get("EXTRACTION_STATUS") == "COMPLETE":
            return response_document(document, True)
        if document.get("EXTRACTION_VERSION") != VERSION:
            raise ValueError("Version d'extraction non prise en charge")
        metadata = json.loads(_read_uri(document["METADATA_STORAGE_URI"]))
        chunks = metadata["chunks"]
        index = document.get("NEXT_CHUNK") or 0
        if index >= len(chunks):
            raise ValueError("État d'extraction incohérent")
        try:
            cache_path = f"company-watch/documents/{document_id}/extraction/{index:05d}.json"
            blob = bucket.blob(cache_path)
            try:
                raw = blob.download_as_text(encoding="utf-8")
                candidates = parse_candidates(raw)
            except NotFound:
                candidates, raw = extract_candidates(chunks[index], metadata)
                _upload(cache_path, raw.encode("utf-8"), "application/json")
            units = validate_candidates(candidates, chunks[index], index)
            # Une transaction par segment : unités + curseur sont validés ensemble.
            _query(f"""BEGIN TRANSACTION;
                ASSERT (SELECT COUNT(*) FROM `{DOCUMENT}` WHERE ID_DOCUMENT=@id
                    AND NEXT_CHUNK=@current AND EXTRACTION_VERSION=@version) = 1
                    AS 'Le curseur d’extraction a changé ; reprendre le traitement';
                MERGE `{UNIT}` T
                USING (
                  SELECT JSON_VALUE(u, '$.unit_id') AS UNIT_ID,
                    JSON_VALUE(u, '$.fact') AS FACT, JSON_VALUE(u, '$.quote') AS QUOTE,
                    JSON_VALUE(u, '$.status') AS VERIFICATION_STATUS,
                    JSON_VALUE(u, '$.kind') AS KIND, JSON_VALUE(u, '$.geography') AS GEOGRAPHY,
                    JSON_VALUE(u, '$.period') AS PERIOD, JSON_VALUE(u, '$.source_locator') AS SOURCE_LOCATOR,
                    SAFE_CAST(JSON_VALUE(u, '$.source_start') AS INT64) AS SOURCE_START,
                    SAFE_CAST(JSON_VALUE(u, '$.source_end') AS INT64) AS SOURCE_END,
                    SAFE_CAST(JSON_VALUE(u, '$.chunk_index') AS INT64) AS CHUNK_INDEX,
                    SAFE_CAST(JSON_VALUE(u, '$.candidate_index') AS INT64) AS CANDIDATE_INDEX,
                    JSON_VALUE(u, '$.reason') AS VERIFICATION_REASON,
                    SAFE_CAST(JSON_VALUE(u, '$.match_score') AS FLOAT64) AS MATCH_SCORE
                  FROM UNNEST(JSON_QUERY_ARRAY(PARSE_JSON(@payload))) u
                ) S ON T.ID_DOCUMENT=@id AND T.UNIT_ID=S.UNIT_ID
                WHEN NOT MATCHED THEN INSERT (
                  ID_DOCUMENT, UNIT_ID, PDF_PAGE, FACT, QUOTE, VERIFICATION_STATUS, KIND,
                  GEOGRAPHY, PERIOD, SOURCE_LOCATOR, SOURCE_START, SOURCE_END, CHUNK_INDEX,
                  CANDIDATE_INDEX, VERIFICATION_REASON, MATCH_SCORE, CREATED_AT)
                VALUES (@id, S.UNIT_ID, NULL, S.FACT, S.QUOTE, S.VERIFICATION_STATUS, S.KIND,
                  S.GEOGRAPHY, S.PERIOD, S.SOURCE_LOCATOR, S.SOURCE_START, S.SOURCE_END,
                  S.CHUNK_INDEX, S.CANDIDATE_INDEX, S.VERIFICATION_REASON, S.MATCH_SCORE, CURRENT_TIMESTAMP());
                UPDATE `{DOCUMENT}` SET NEXT_CHUNK=@next,
                  EXTRACTION_STATUS=IF(@next >= CHUNK_COUNT, 'COMPLETE', 'PENDING'),
                  EXTRACTION_ERROR=NULL, UPDATED_AT=CURRENT_TIMESTAMP() WHERE ID_DOCUMENT=@id;
                COMMIT TRANSACTION;""",
                [_p("id", "STRING", document_id), _p("next", "INT64", index + 1),
                 _p("current", "INT64", index), _p("version", "STRING", VERSION),
                 _p("payload", "STRING", json.dumps(units, ensure_ascii=False))])
        except Exception as exc:
            _query(f"""UPDATE `{DOCUMENT}` SET EXTRACTION_STATUS='ERROR', EXTRACTION_ERROR=@error,
                UPDATED_AT=CURRENT_TIMESTAMP() WHERE ID_DOCUMENT=@id""",
                [_p("id", "STRING", document_id), _p("error", "STRING", str(exc)[:3000])])
            raise
        return response_document(get_document(company_id, watch_id, document_id))


def list_publications(company_id: str, watch_id: str, offset=0, limit=50) -> dict:
    rows = _query(f"""SELECT d.ID_DOCUMENT, d.TITLE, d.SOURCE_URL, d.PUBLISHED_AT, d.COLLECTED_AT,
          d.EXTRACTION_STATUS, d.EXTRACTION_ERROR, d.NEXT_CHUNK, d.CHUNK_COUNT,
          (SELECT COUNT(*) FROM `{UNIT}` u WHERE u.ID_DOCUMENT=d.ID_DOCUMENT) AS UNIT_COUNT,
          (SELECT COUNTIF(VERIFICATION_STATUS != 'VERIFIED') FROM `{UNIT}` u
            WHERE u.ID_DOCUMENT=d.ID_DOCUMENT) AS REVIEW_COUNT
        FROM `{DOCUMENT}` d WHERE ID_COMPANY=@company AND ID_COMPANY_WATCH=@watch
        ORDER BY COLLECTED_AT DESC, ID_DOCUMENT LIMIT @limit OFFSET @offset""",
        [_p("company", "STRING", company_id), _p("watch", "STRING", watch_id),
         _p("limit", "INT64", limit + 1), _p("offset", "INT64", offset)])
    return {"items": [{k.lower(): v for k, v in dict(row).items()} for row in rows[:limit]],
            "has_more": len(rows) > limit}


def publication_detail(company_id: str, watch_id: str, document_id: str, offset=0, limit=100) -> dict:
    document = get_document(company_id, watch_id, document_id)
    rows = _query(f"""SELECT * FROM `{UNIT}` WHERE ID_DOCUMENT=@id
        ORDER BY CHUNK_INDEX, CANDIDATE_INDEX LIMIT @limit OFFSET @offset""",
        [_p("id", "STRING", document_id), _p("limit", "INT64", limit + 1), _p("offset", "INT64", offset)])
    return {**response_document(document), "text": _read_uri(document["TEXT_STORAGE_URI"]),
            "units": [{k.lower(): v for k, v in dict(row).items()} for row in rows[:limit]],
            "has_more": len(rows) > limit,
            "warning": "VERIFIED valide la présence de la citation, pas la vérité ni l'interprétation du fait."}
