"""Qualify new Library posts in the background and backfill a selected period."""

import argparse
import json
import logging
import threading
from datetime import date, timedelta

from fastapi import HTTPException
from google.cloud import bigquery

from core.company import library_post_funnel as funnel
from core.library import company_watch_library as library

logger = logging.getLogger(__name__)
RETRY = f"{library.BASE}.RATECARD_LIBRARY_POST_TRIAGE_RETRY"
START = f"{library.BASE}.RATECARD_LIBRARY_POST_TRIAGE_START"
BATCH_SIZE = 20
POLL_SECONDS = 60
_WAKE = threading.Event()
_STOP = threading.Event()
_GUARD = threading.Lock()
_thread = None


def qualify_batch(*, company_ids=None, start=None, end=None, limit=BATCH_SIZE):
    """Process a bounded set of eligible posts from durable Library state."""
    if not 1 <= limit <= 100:
        raise ValueError("La taille du lot doit être comprise entre 1 et 100")
    params = [library._p("version", "STRING", funnel.VERSION),
              library._p("limit", "INT64", limit)]
    if company_ids is None:
        scope = f"""EXISTS (
            SELECT 1 FROM `{library.BASE}.RATECARD_COMPANY_WATCH_DISCOVERY` q
            WHERE q.ID_DOCUMENT=d.ID_DOCUMENT
              AND q.ID_COMPANY=d.ID_COMPANY
              AND q.ID_COMPANY_WATCH=d.ID_COMPANY_WATCH
              AND q.LIBRARY_STATUS='IMPORTED'
              AND q.DATE_FOUND >= (SELECT MIN(STARTED_AT) FROM `{START}`)
        )"""
    else:
        if not company_ids or start is None or end is None or end < start:
            raise ValueError("Indiquez les sociétés et une période de publication valide")
        scope = """d.ID_COMPANY IN UNNEST(@companies)
            AND d.PUBLISHED_AT >= TIMESTAMP(@start, 'Europe/Paris')
            AND d.PUBLISHED_AT < TIMESTAMP(@end, 'Europe/Paris')"""
        params += [
            bigquery.ArrayQueryParameter("companies", "STRING", sorted(set(company_ids))),
            library._p("start", "DATE", start),
            library._p("end", "DATE", end + timedelta(days=1)),
        ]

    rows = library._query(f"""
        SELECT d.ID_COMPANY, d.ID_DOCUMENT, c.NAME AS COMPANY_NAME, d.TEXT_STORAGE_URI
        FROM `{library.DOCUMENT}` d
        JOIN `{library.BASE}.RATECARD_COMPANY` c USING (ID_COMPANY)
        LEFT JOIN `{library.BASE}.RATECARD_COMPANY_WATCH` w
            ON w.ID_COMPANY=d.ID_COMPANY AND w.ID_COMPANY_WATCH=d.ID_COMPANY_WATCH
        WHERE d.DOCUMENT_TYPE='LINKEDIN' AND d.ID_COMPANY_WATCH IS NOT NULL
          AND COALESCE(d.EDITORIAL_STATUS, 'ACTIVE')='ACTIVE'
          AND COALESCE(d.SOURCE_ROLE, w.SOURCE_ROLE,
              IF(w.ID_CONTACT IS NOT NULL, 'EMPLOYEE', 'CORPORATE'))='EMPLOYEE'
          AND d.TEXT_STORAGE_URI IS NOT NULL
          AND {scope}
          AND NOT EXISTS (
              SELECT 1 FROM `{funnel.TABLE}` v
              WHERE v.ID_COMPANY=d.ID_COMPANY AND v.ID_DOCUMENT=d.ID_DOCUMENT
                AND v.VERSION=@version
          )
          AND NOT EXISTS (
              SELECT 1 FROM `{RETRY}` r
              WHERE r.ID_COMPANY=d.ID_COMPANY AND r.ID_DOCUMENT=d.ID_DOCUMENT
                AND r.VERSION=@version AND r.NEXT_ATTEMPT_AT > CURRENT_TIMESTAMP()
          )
        ORDER BY d.CREATED_AT, d.ID_DOCUMENT
        LIMIT @limit
    """, params)

    result = {"selectionnes": len(rows), "qualifies": 0, "reutilises": 0,
              "occupes": 0, "a_reprendre": 0}
    for row in rows:
        try:
            verdict = funnel._verdict(row)
        except HTTPException as exc:
            if exc.status_code != 409:
                _defer(row)
                result["a_reprendre"] += 1
            else:
                result["occupes"] += 1
        except Exception:
            _defer(row)
            result["a_reprendre"] += 1
        else:
            result["reutilises" if verdict["reutilise"] else "qualifies"] += 1
    return result


def _defer(row):
    logger.exception("Qualification du post à reprendre : %s", row["ID_DOCUMENT"])
    library._query(f"""
        MERGE `{RETRY}` r
        USING (SELECT @company AS ID_COMPANY, @document AS ID_DOCUMENT, @version AS VERSION) s
        ON r.ID_COMPANY=s.ID_COMPANY AND r.ID_DOCUMENT=s.ID_DOCUMENT AND r.VERSION=s.VERSION
        WHEN MATCHED THEN UPDATE SET NEXT_ATTEMPT_AT=TIMESTAMP_ADD(CURRENT_TIMESTAMP(), INTERVAL 15 MINUTE)
        WHEN NOT MATCHED THEN INSERT (ID_COMPANY, ID_DOCUMENT, VERSION, NEXT_ATTEMPT_AT)
          VALUES (s.ID_COMPANY, s.ID_DOCUMENT, s.VERSION,
                  TIMESTAMP_ADD(CURRENT_TIMESTAMP(), INTERVAL 15 MINUTE))
    """, [
        library._p("company", "STRING", row["ID_COMPANY"]),
        library._p("document", "STRING", row["ID_DOCUMENT"]),
        library._p("version", "STRING", funnel.VERSION),
    ])


def _run():
    while not _STOP.is_set():
        _WAKE.clear()
        try:
            batch = qualify_batch()
            if batch["selectionnes"] == BATCH_SIZE and batch["occupes"] == 0:
                continue
        except Exception:
            logger.exception("File de qualification des posts indisponible")
        _WAKE.wait(POLL_SECONDS)


def start_post_worker():
    """Start one thread per API process. The existing GCS lock serializes each post."""
    global _thread
    with _GUARD:
        if _thread is None or not _thread.is_alive():
            _STOP.clear()
            _thread = threading.Thread(target=_run, name="library-post-triage", daemon=True)
            _thread.start()


def stop_post_worker():
    _STOP.set()
    _WAKE.set()


def wake_post_worker():
    start_post_worker()
    _WAKE.set()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--company", action="append", required=True, metavar="ID_COMPANY")
    parser.add_argument("--start", required=True, type=date.fromisoformat)
    parser.add_argument("--end", required=True, type=date.fromisoformat)
    parser.add_argument("--limit", type=int, default=50)
    args = parser.parse_args()
    batch = qualify_batch(company_ids=args.company, start=args.start, end=args.end, limit=args.limit)
    print(json.dumps(batch, ensure_ascii=False))
    return int(bool(batch["a_reprendre"]))
