"""Index media indicators from saved LinkedIn capture JSON."""

import argparse
import json
import logging
from concurrent.futures import ThreadPoolExecutor

from core.library import company_watch_library as library

TABLE = f"{library.BASE}.RATECARD_LIBRARY_POST_MEDIA"
logger = logging.getLogger(__name__)


def _positive_int(value):
    return value if type(value) is int and value > 0 else None


def read_indicators(uri):
    record = json.loads(library._read_uri(uri))
    if not isinstance(record, dict):
        raise ValueError("Capture LinkedIn inattendue")
    pages = _positive_int(record.get("document_page_count"))
    duration = _positive_int(record.get("video_duration"))
    return {
        "has_video": bool(record.get("videos") or record.get("video_thumbnail") or duration),
        "has_document": bool(record.get("document_cover_image") or pages),
        "document_page_count": pages,
        "video_duration": duration,
    }


def save(items):
    if not items:
        return
    library._query(f"""
        MERGE `{TABLE}` m
        USING (
            SELECT JSON_VALUE(j,'$.id') AS ID_DOCUMENT, JSON_VALUE(j,'$.uri') AS STORAGE_URI,
                   SAFE_CAST(JSON_VALUE(j,'$.has_video') AS BOOL) AS HAS_VIDEO,
                   SAFE_CAST(JSON_VALUE(j,'$.has_document') AS BOOL) AS HAS_DOCUMENT,
                   SAFE_CAST(JSON_VALUE(j,'$.document_page_count') AS INT64) AS DOCUMENT_PAGE_COUNT,
                   SAFE_CAST(JSON_VALUE(j,'$.video_duration') AS INT64) AS VIDEO_DURATION
            FROM UNNEST(JSON_QUERY_ARRAY(@items)) j
            QUALIFY ROW_NUMBER() OVER (
                PARTITION BY JSON_VALUE(j,'$.id'), JSON_VALUE(j,'$.uri')
            )=1
        ) s
        ON m.ID_DOCUMENT=s.ID_DOCUMENT AND m.STORAGE_URI=s.STORAGE_URI
        WHEN NOT MATCHED THEN INSERT (
            ID_DOCUMENT, STORAGE_URI, HAS_VIDEO, HAS_DOCUMENT, DOCUMENT_PAGE_COUNT, VIDEO_DURATION
        ) VALUES (
            s.ID_DOCUMENT, s.STORAGE_URI, s.HAS_VIDEO, s.HAS_DOCUMENT,
            s.DOCUMENT_PAGE_COUNT, s.VIDEO_DURATION
        )
    """, [library._p("items", "STRING", json.dumps(items))])


def index_documents(document_ids=None, *, limit=100, after=""):
    from google.cloud.bigquery import ArrayQueryParameter

    scope = "d.ID_DOCUMENT IN UNNEST(@ids)" if document_ids else "TRUE"
    params = [library._p("limit", "INT64", limit), library._p("after", "STRING", after)]
    if document_ids:
        params.append(ArrayQueryParameter("ids", "STRING", document_ids))
    rows = library._query(f"""
        SELECT d.ID_DOCUMENT, d.STORAGE_URI
        FROM `{library.DOCUMENT}` d
        LEFT JOIN `{TABLE}` m
          ON m.ID_DOCUMENT=d.ID_DOCUMENT AND m.STORAGE_URI=d.STORAGE_URI
        WHERE d.DOCUMENT_TYPE='LINKEDIN' AND d.ID_COMPANY_WATCH IS NOT NULL
          AND ENDS_WITH(d.STORAGE_URI, '.json')
          AND d.ID_DOCUMENT>@after AND m.ID_DOCUMENT IS NULL AND {scope}
        ORDER BY d.ID_DOCUMENT LIMIT @limit
    """, params)

    def prepare(row):
        try:
            return {"id": row["ID_DOCUMENT"], "uri": row["STORAGE_URI"],
                    **read_indicators(row["STORAGE_URI"])}
        except Exception:
            logger.exception("Média LinkedIn non indexé pour %s", row["ID_DOCUMENT"])
            return None

    with ThreadPoolExecutor(max_workers=4) as pool:
        items = [item for item in pool.map(prepare, rows) if item is not None]
    save(items)
    return len(items), len(rows) - len(items), rows[-1]["ID_DOCUMENT"] if rows else None


def index_arrivals(document_ids):
    if document_ids:
        try:
            index_documents(document_ids, limit=len(document_ids))
        except Exception:
            logger.exception("Indexation média différée")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--batches", type=int, default=5)
    args = parser.parse_args()
    if args.batches < 1:
        parser.error("--batches doit être positif")
    cursor = ""
    indexed = failures = 0
    for _ in range(args.batches):
        count, failed, cursor = index_documents(after=cursor)
        indexed += count
        failures += failed
        if cursor is None:
            break
    print(f"{indexed} captures indexées, {failures} en échec.")
    return int(bool(failures))


if __name__ == "__main__":
    raise SystemExit(main())
