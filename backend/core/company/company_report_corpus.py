"""Corpus de veille par société et par mois, avec brouillon versionné."""

import hashlib
import json
import re
from datetime import date

from fastapi import HTTPException
from google.api_core.exceptions import NotFound, PreconditionFailed

from core.company import watch_discovery_service as discovery
from core.company.library_post_funnel import TABLE as VERDICT, VERSION
from core.company.library_post_review import EMPLOYEE_ROLE, LATEST
from core.library import company_watch_library as library
from utils.gcs import bucket


def _scope(company_id, month):
    if not company_id.strip() or not re.fullmatch(r"[0-9]{4}-[0-9]{2}", month):
        raise ValueError("Une société et un mois au format AAAA-MM sont requis.")
    start = date.fromisoformat(month + "-01")
    end = date(start.year + (start.month == 12), start.month % 12 + 1, 1)
    key = hashlib.sha256(f"{library.BASE}|{company_id}".encode()).hexdigest()
    return start, end, f"company-reports/corpus/{key}/{month}.json"


def _candidates(company_id, start, end):
    return [dict(row) for row in library._query(f"""
        WITH auto AS (
            SELECT ID_COMPANY, ID_DOCUMENT, VERDICT
            FROM `{VERDICT}`
            WHERE ID_COMPANY=@company AND VERSION=@version
            QUALIFY ROW_NUMBER() OVER (
                PARTITION BY ID_COMPANY, ID_DOCUMENT ORDER BY CREATED_AT DESC, VERDICT, TYPE_PRINCIPAL
            )=1
        ), page_changes AS (
            SELECT d.ID_DISCOVERY, d.ID_DOCUMENT, d.TITLE, d.URL, d.DATE_FOUND, d.CHANGE_TYPE
            FROM `{discovery.DISCOVERY}` d
            JOIN `{discovery.WATCH}` w USING (ID_COMPANY, ID_COMPANY_WATCH)
            WHERE d.ID_COMPANY=@company AND d.CHANGE_TYPE IN ('NEW_PAGE','UPDATED_PAGE')
              AND COALESCE(d.STATUS,'')!='DISMISSED'
              AND COALESCE(w.SOURCE_ROLE,'CORPORATE')!='EMPLOYEE' AND w.ID_CONTACT IS NULL
              AND NOT REGEXP_CONTAINS(LOWER(COALESCE(d.URL,'')), r'^https?://([a-z0-9-]+[.])*linkedin[.]com([/?#]|$)')
              AND d.DATE_FOUND>=TIMESTAMP(@start,'Europe/Paris')
              AND d.DATE_FOUND<TIMESTAMP(@end,'Europe/Paris')
        ), documents AS (
            SELECT CONCAT('document:', d.ID_DOCUMENT) AS id, d.ID_DOCUMENT AS document_id,
                   CAST(NULL AS STRING) AS discovery_id, d.TITLE AS title, d.SOURCE_URL AS url,
                   d.AUTHOR_NAME AS author, COALESCE(d.PUBLISHED_AT,d.COLLECTED_AT,d.CREATED_AT) AS source_at,
                   IF(d.PUBLISHED_AT IS NULL,'COLLECTION','PUBLICATION') AS date_kind,
                   CASE
                     WHEN d.DOCUMENT_TYPE='MENTION' THEN 'MENTION'
                     WHEN d.DOCUMENT_TYPE='LINKEDIN' AND {EMPLOYEE_ROLE} THEN 'LINKEDIN_EMPLOYEE'
                     WHEN d.DOCUMENT_TYPE='LINKEDIN' THEN 'LINKEDIN_CORPORATE'
                     ELSE 'SITE_PUBLICATION'
                   END AS source_kind,
                   COALESCE(r.VERDICT,v.VERDICT) AS verdict, CAST(NULL AS STRING) AS change_type
            FROM `{library.DOCUMENT}` d
            LEFT JOIN `{discovery.WATCH}` w USING (ID_COMPANY, ID_COMPANY_WATCH)
            LEFT JOIN auto v USING (ID_COMPANY, ID_DOCUMENT)
            LEFT JOIN ({LATEST}) r USING (ID_COMPANY, ID_DOCUMENT)
            WHERE d.ID_COMPANY=@company AND COALESCE(d.EDITORIAL_STATUS,'ACTIVE')='ACTIVE'
              AND (d.DOCUMENT_TYPE='MENTION' OR d.ID_COMPANY_WATCH IS NOT NULL)
              AND (d.DOCUMENT_TYPE IN ('MENTION','LINKEDIN') OR NOT COALESCE({EMPLOYEE_ROLE}, FALSE))
              AND NOT EXISTS (
                SELECT 1 FROM `{discovery.DISCOVERY}` x
                WHERE x.ID_COMPANY=d.ID_COMPANY AND x.ID_DOCUMENT=d.ID_DOCUMENT
                  AND x.CHANGE_TYPE IN ('NEW_PAGE','UPDATED_PAGE')
              )
        )
        SELECT *, source_kind IN ('LINKEDIN_CORPORATE','LINKEDIN_EMPLOYEE') AS suggested
        FROM documents
        WHERE source_at>=TIMESTAMP(@start,'Europe/Paris') AND source_at<TIMESTAMP(@end,'Europe/Paris')
          AND (source_kind!='LINKEDIN_EMPLOYEE' OR verdict IN ('SIGNAL_SOCIETE','PRISE_DE_PAROLE_METIER'))
        UNION ALL
        SELECT CONCAT('discovery:',p.ID_DISCOVERY), p.ID_DOCUMENT, p.ID_DISCOVERY, p.TITLE, p.URL,
               NULL, p.DATE_FOUND, 'OBSERVATION', 'SITE_CHANGE', NULL, p.CHANGE_TYPE, FALSE
        FROM page_changes p
        LEFT JOIN `{library.DOCUMENT}` d ON d.ID_COMPANY=@company AND d.ID_DOCUMENT=p.ID_DOCUMENT
        WHERE p.ID_DOCUMENT IS NULL OR COALESCE(d.EDITORIAL_STATUS,'ACTIVE')='ACTIVE'
        ORDER BY source_at DESC, id
    """, [
        library._p("company", "STRING", company_id),
        library._p("start", "DATE", start),
        library._p("end", "DATE", end),
        library._p("version", "STRING", VERSION),
    ])]


def _read_draft(path):
    blob = bucket.blob(path)
    try:
        blob.reload()
        revision = int(blob.generation)
        return json.loads(blob.download_as_text(if_generation_match=revision)), str(revision)
    except NotFound:
        return None, "0"
    except PreconditionFailed as exc:
        raise HTTPException(409, "Le brouillon a changé. Rechargez le corpus.") from exc


def get_corpus(company_id, month):
    start, end, path = _scope(company_id, month)
    candidates = _candidates(company_id, start, end)
    draft, revision = _read_draft(path)
    available = {item["id"] for item in candidates}
    saved_ids = draft["selected_ids"] if draft is not None else [
        item["id"] for item in candidates if item["suggested"]
    ]
    return {
        "candidates": candidates, "revision": revision,
        "selected_ids": [id for id in saved_ids if id in available],
        "unavailable_count": sum(id not in available for id in saved_ids),
    }


def save_corpus(company_id, month, selected_ids, revision):
    start, end, path = _scope(company_id, month)
    if not re.fullmatch(r"[0-9]{1,24}", revision):
        raise ValueError("Révision de brouillon invalide.")
    available = {item["id"] for item in _candidates(company_id, start, end)}
    if len(selected_ids) != len(set(selected_ids)) or not set(selected_ids) <= available:
        raise HTTPException(409, "La sélection a changé. Rechargez le corpus avant de l’enregistrer.")
    blob = bucket.blob(path)
    try:
        blob.upload_from_string(
            json.dumps({"company_id": company_id, "month": month, "selected_ids": selected_ids}),
            content_type="application/json", if_generation_match=int(revision),
        )
    except PreconditionFailed as exc:
        raise HTTPException(409, "Un autre enregistrement a modifié le brouillon. Rechargez le corpus.") from exc
    return {"revision": str(blob.generation)}
