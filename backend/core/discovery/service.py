from typing import List, Dict
from datetime import datetime
from urllib.parse import urlparse

import uuid
import requests

from bs4 import BeautifulSoup

from config import BQ_PROJECT, BQ_DATASET

from utils.bigquery_utils import (
    query_bq,
    get_bigquery_client,
)

from google.cloud import bigquery


# ============================================================
# TABLES
# ============================================================

TABLE_SOURCE = (
    f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_SOURCE"
)

TABLE_DISCOVERY = (
    f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_SOURCE_DISCOVERY"
)

TABLE_RAW = (
    f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_CONTENT_RAW"
)

# ============================================================
# HTTP
# ============================================================

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 "
        "(Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 "
        "(KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}


# ============================================================
# DISCOVERY EXISTS
# ============================================================

def discovery_url_exists(url: str) -> bool:

    sql = f"""
        SELECT 1
        FROM `{TABLE_DISCOVERY}`
        WHERE URL = @url
        LIMIT 1
    """

    rows = query_bq(
        sql,
        {"url": url},
    )

    return len(rows) > 0


# ============================================================
# RAW EXISTS
# ============================================================

def raw_url_exists(url: str) -> bool:

    sql = f"""
        SELECT 1
        FROM `{TABLE_RAW}`
        WHERE SOURCE_URL = @url
        LIMIT 1
    """

    rows = query_bq(
        sql,
        {"url": url},
    )

    return len(rows) > 0


# ============================================================
# INSERT DISCOVERY
# ============================================================

def insert_discovery_url(
    source_id: str,
    url: str,
    title: str,
):

    client = get_bigquery_client()

    payload = [{
        "ID_DISCOVERY": str(uuid.uuid4()),
        "SOURCE_ID": source_id,
        "URL": url,
        "TITLE": title,
        "STATUS": "NEW",
        "DATE_FOUND": datetime.utcnow().isoformat(),
        "CREATED_AT": datetime.utcnow().isoformat(),
    }]

    client.load_table_from_json(
        payload,
        TABLE_DISCOVERY,
        job_config=bigquery.LoadJobConfig(
            write_disposition="WRITE_APPEND"
        ),
    ).result()


def get_existing_discovery_urls():

    sql = f"""
        SELECT URL
        FROM `{TABLE_DISCOVERY}`
    """

    rows = query_bq(sql)

    return {
        r["URL"]
        for r in rows
        if r.get("URL")
    }


def get_existing_raw_urls():

    sql = f"""
        SELECT SOURCE_URL
        FROM `{TABLE_RAW}`
        WHERE SOURCE_URL IS NOT NULL
    """

    rows = query_bq(sql)

    return {
        r["SOURCE_URL"]
        for r in rows
        if r.get("SOURCE_URL")
    }


# ============================================================
# EXTRACT URLS FROM PAGE
# ============================================================

def extract_urls_from_page(
    page_url: str,
) -> List[Dict]:

    response = requests.get(
        page_url,
        headers=HEADERS,
        timeout=20,
    )

    response.raise_for_status()

    soup = BeautifulSoup(
        response.text,
        "html.parser",
    )

    page_domain = urlparse(
        page_url
    ).netloc.lower()

    results = []
    seen = set()

    for link in soup.find_all("a"):

        href = link.get("href")

        if not href:
            continue

        if not href.startswith("http"):
            continue

        href_domain = (
            urlparse(href)
            .netloc
            .lower()
        )

        if href_domain != page_domain:
            continue

        if "#" in href:
            continue

        href_lower = href.lower()

        excluded = [
            "/tag/",
            "/tags/",
            "/category/",
            "/categories/",
            "/author/",
            "/authors/",
            "/about",
            "/contact",
            "/privacy",
            "/terms",
            "/login",
            "/account",
        ]

        if any(
            x in href_lower
            for x in excluded
        ):
            continue

        title = (
            link.get_text(strip=True)
            or href
        )

        if href in seen:
            continue

        seen.add(href)

        results.append(
            {
                "url": href,
                "title": title,
            }
        )

    return results


# ============================================================
# GET SOURCE
# ============================================================

def get_source_for_scan(
    source_id: str,
):

    sql = f"""
        SELECT
            SOURCE_ID,
            NAME,
            DOMAIN,
            ACQUISITION_MODE
        FROM `{TABLE_SOURCE}`
        WHERE SOURCE_ID = @source_id
        LIMIT 1
    """

    rows = query_bq(
        sql,
        {
            "source_id": source_id,
        },
    )

    if not rows:
        return None

    return rows[0]


# ============================================================
# SCAN SOURCE
# ============================================================

def scan_source(
    source_id: str,
):

    source = get_source_for_scan(
        source_id
    )

    if not source:
        raise Exception(
            "Source introuvable"
        )

    domain = source.get(
        "DOMAIN"
    )

    if not domain:
        raise Exception(
            "DOMAIN manquant"
        )

    urls = extract_urls_from_page(
        domain
    )

    discovered = 0

    for item in urls:

        url = item["url"]

        if discovery_url_exists(url):
            continue

        if raw_url_exists(url):
            continue

        insert_discovery_url(
            source_id=source_id,
            url=url,
            title=item["title"],
        )

        discovered += 1

    return {
        "status": "ok",
        "scanned_sources": 1,
        "discovered_urls": discovered,
    }


# ============================================================
# SCAN ALL SOURCES
# ============================================================

def scan_all_sources():

    sql = f"""
        SELECT
            SOURCE_ID
        FROM `{TABLE_SOURCE}`
        WHERE DOMAIN IS NOT NULL
          AND DOMAIN != ''
    """

    rows = query_bq(sql)

    total_discovered = 0

    for row in rows:

        try:

            result = scan_source(
                row["SOURCE_ID"]
            )

            total_discovered += result[
                "discovered_urls"
            ]

        except Exception as e:

            print(
                "[DISCOVERY]",
                row["SOURCE_ID"],
                e,
            )

    return {
        "status": "ok",
        "scanned_sources": len(rows),
        "discovered_urls": total_discovered,
    }


# ============================================================
# LIST DISCOVERY
# ============================================================

def list_discovery_items():

    sql = f"""
        SELECT
            d.ID_DISCOVERY,
            d.SOURCE_ID,
            d.URL,
            d.TITLE,
            d.STATUS,
            d.DATE_FOUND,
            d.CREATED_AT,

            s.NAME AS SOURCE_NAME

        FROM `{TABLE_DISCOVERY}` d

        LEFT JOIN `{TABLE_SOURCE}` s
          ON d.SOURCE_ID = s.SOURCE_ID

        ORDER BY d.DATE_FOUND DESC
    """

    rows = query_bq(sql)

    return [
        {
            "id_discovery": r["ID_DISCOVERY"],
            "source_id": r["SOURCE_ID"],
            "source_name": r.get(
                "SOURCE_NAME"
            ),
            "url": r["URL"],
            "title": r.get("TITLE"),
            "status": r["STATUS"],
            "date_found": r.get(
                "DATE_FOUND"
            ),
            "created_at": r.get(
                "CREATED_AT"
            ),
        }
        for r in rows
    ]


# ============================================================
# STORE DISCOVERY URLS
# ============================================================

def store_discovery_urls(
    discovery_ids: List[str],
):

    return {
        "status": "not_implemented",
        "stored": 0,
        "skipped": 0,
        "errors": 0,
    }


# ============================================================
# IGNORE DISCOVERY URLS
# ============================================================

def ignore_discovery_urls(
    discovery_ids: List[str],
):

    return {
        "status": "not_implemented",
        "ignored": 0,
    }

def dismiss_discovery(
    id_discovery: str,
):

    sql = f"""
        UPDATE `{TABLE_DISCOVERY}`
        SET STATUS = 'DISMISSED'
        WHERE ID_DISCOVERY = @id
    """

    query_bq(
        sql,
        {
            "id": id_discovery,
        },
    )

    return True
