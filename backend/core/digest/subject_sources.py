from urllib.parse import urlsplit

from config import BQ_DATASET, BQ_PROJECT
from utils.bigquery_utils import query_bq

DATASET = f"{BQ_PROJECT}.{BQ_DATASET}"
PUBLICATION_NAMES = {
    "linkedin.com": "LinkedIn",
    "thedrinksbusiness.com": "The Drinks Business",
}


def _source_domain(url):
    try:
        hostname = urlsplit(url or "").hostname
    except ValueError:
        return None
    if not hostname:
        return None
    hostname = hostname.lower().removeprefix("www.")
    for domain, name in PUBLICATION_NAMES.items():
        if hostname == domain or hostname.endswith("." + domain):
            return name
    return hostname


def add_subject_source_names(document):
    contents = [
        content for card in document.get("cards", [])
        for content in card.get("contents", [])
        if not content.get("source_name")
    ]
    if not contents:
        return document
    ids = list(dict.fromkeys(content["id"] for content in contents))
    rows = query_bq(sql=f"""
        WITH sources AS (
          SELECT CAST(SOURCE_ID AS STRING) AS id, TO_JSON_STRING(s) AS metadata
          FROM `{DATASET}.RATECARD_SOURCE` s
        )
        SELECT c.id_content AS id, c.source_url AS source_url,
               c.source_title AS source_title,
               COALESCE(
                 NULLIF(TRIM(JSON_VALUE(s.metadata, '$.NAME')), ''),
                 NULLIF(TRIM(JSON_VALUE(s.metadata, '$.SOURCE_NAME')), ''),
                 NULLIF(TRIM(JSON_VALUE(s.metadata, '$.name')), ''),
                 NULLIF(TRIM(JSON_VALUE(s.metadata, '$.source_name')), ''),
                 NULLIF(TRIM(JSON_VALUE(s.metadata, '$.LABEL')), '')
               ) AS source_name
        FROM `{DATASET}.RATECARD_CONTENT_ENRICHED` c
        LEFT JOIN sources s ON s.id = CAST(c.source_id AS STRING)
        WHERE c.id_content IN UNNEST(@ids)
    """, params={"ids": ids}) or []
    by_id = {row["id"]: row for row in rows}
    for content in contents:
        metadata = by_id.get(content["id"], {})
        for field in ("source_url", "source_title"):
            if not content.get(field) and metadata.get(field):
                content[field] = metadata[field]
        content["source_name"] = metadata.get("source_name") or _source_domain(content.get("source_url"))
    return document
