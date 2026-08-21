from typing import List, Dict
from datetime import datetime
import uuid
from config import BQ_PROJECT, BQ_DATASET

from utils.bigquery_utils import (
    query_bq,
    get_bigquery_client,
)

from core.acquisition.storage_service import (
    insert_raw_rows,
)
from core.discovery.router import (
    discover_urls,
)

from core.acquisition.parser_service import (
    parse_article_from_url,
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

TABLE_SOURCE_UNIVERSE = (
    f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_SOURCE_UNIVERSE"
)


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

    urls = discover_urls(
        source
    )

    # ============================================================
    # 🔥 PERFORMANCE
    # Charge une seule fois les URLs existantes
    # ============================================================

    existing_discovery = (
        get_existing_discovery_urls()
    )

    existing_raw = (
        get_existing_raw_urls()
    )

    discovered = 0

    for item in urls:

        url = item["url"]

        if url in existing_discovery:
            continue

        if url in existing_raw:
            continue

        insert_discovery_url(
            source_id=source_id,
            url=url,
            title=item["title"],
        )

        # évite les doublons dans le même scan
        existing_discovery.add(url)

        discovered += 1

    return {
        "status": "ok",
        "scanned_sources": 1,
        "discovered_urls": discovered,
    }

# ============================================================
# SCAN ALL SOURCES
# ============================================================

# ============================================================
# SCAN ALL SOURCES
# ============================================================

def scan_all_sources(
    universe_id: str | None = None,
):

    # ========================================================
    # BASE QUERY
    # ========================================================

    sql = f"""
        SELECT DISTINCT
            s.SOURCE_ID
        FROM `{TABLE_SOURCE}` s
    """

    params = {}

    # ========================================================
    # UNIVERSE FILTER
    # ========================================================

    if universe_id:

        sql += f"""
            INNER JOIN `{TABLE_SOURCE_UNIVERSE}` su
                ON su.ID_SOURCE = s.SOURCE_ID
        """

    # ========================================================
    # AUTOMATIC SOURCES
    # ========================================================

    sql += """
        WHERE s.DOMAIN IS NOT NULL
          AND s.DOMAIN != ''
          AND s.ACQUISITION_MODE IS NOT NULL
          AND s.ACQUISITION_MODE != 'MANUAL'
    """

    # ========================================================
    # APPLY UNIVERSE
    # ========================================================

    if universe_id:

        sql += """
          AND su.ID_UNIVERSE = @universe_id
        """

        params["universe_id"] = (
            universe_id
        )

    # ========================================================
    # LOAD SOURCES
    # ========================================================

    rows = query_bq(
        sql,
        params,
    )

    # ========================================================
    # SCAN
    # ========================================================

    total_discovered = 0
    scanned_sources = 0
    failed_sources = 0

    for row in rows:

        try:

            result = scan_source(
                row["SOURCE_ID"]
            )

            total_discovered += (
                result[
                    "discovered_urls"
                ]
            )

            scanned_sources += 1

        except Exception as e:

            failed_sources += 1

            print(
                "[DISCOVERY]",
                row["SOURCE_ID"],
                e,
            )

    # ========================================================
    # RESULT
    # ========================================================

    return {
        "status": "ok",
        "scanned_sources": scanned_sources,
        "failed_sources": failed_sources,
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

        WHERE d.STATUS = 'NEW'

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

# ============================================================
# IGNORE DISCOVERY URLS
# ============================================================

def ignore_discovery_urls(
    discovery_ids: List[str],
):

    if not discovery_ids:

        return {
            "status": "ok",
            "ignored": 0,
        }

    ids_sql = ",".join(
        [f"'{x}'" for x in discovery_ids]
    )

    sql = f"""
        UPDATE `{TABLE_DISCOVERY}`
        SET STATUS = 'DISMISSED'
        WHERE ID_DISCOVERY IN ({ids_sql})
    """

    query_bq(sql)

    return {
        "status": "ok",
        "ignored": len(discovery_ids),
    }

# ============================================================
# STORE DISCOVERY URLS
# ============================================================

def store_discovery_urls(
    discovery_ids: List[str],
):

    if not discovery_ids:

        return {
            "status": "ok",
            "stored": 0,
            "skipped": 0,
            "errors": 0,
        }

    ids_sql = ",".join(
        [f"'{x}'" for x in discovery_ids]
    )

    sql = f"""
        SELECT
            ID_DISCOVERY,
            SOURCE_ID,
            URL,
            TITLE,
            STATUS
        FROM `{TABLE_DISCOVERY}`
        WHERE ID_DISCOVERY IN ({ids_sql})
    """

    rows = query_bq(sql)

    stored = 0
    skipped = 0
    errors = 0

    for row in rows:

        try:

            if row["STATUS"] == "STORED":

                skipped += 1
                continue

            parsed = parse_article_from_url(
                row["URL"]
            )

            insert_raw_rows(
                rows=[
                    {
                        "TITLE": parsed["TITLE"],
                        "DATE_SOURCE": parsed.get(
                            "DATE_SOURCE"
                        ),
                        "RAW_TEXT": parsed[
                            "RAW_TEXT"
                        ],
                        "SOURCE_URL": row["URL"],
                    }
                ],
                id_source=row["SOURCE_ID"],
                import_type="URL",
            )

            query_bq(
                f"""
                UPDATE `{TABLE_DISCOVERY}`
                SET STATUS = 'STORED'
                WHERE ID_DISCOVERY = @id
                """,
                {
                    "id": row["ID_DISCOVERY"],
                },
            )

            stored += 1

        except Exception as e:

            print(
                "[DISCOVERY STORE]",
                row["URL"],
                e,
            )

            errors += 1

    return {
        "status": "ok",
        "stored": stored,
        "skipped": skipped,
        "errors": errors,
    }

# ============================================================
# MANUAL REVIEW
# ============================================================

def mark_discovery_manual(
    discovery_ids: List[str],
):

    if not discovery_ids:

        return {
            "status": "ok",
            "manual": 0,
        }

    ids_sql = ",".join(
        [f"'{x}'" for x in discovery_ids]
    )

    sql = f"""
        UPDATE `{TABLE_DISCOVERY}`
        SET STATUS = 'MANUAL_REVIEW'
        WHERE ID_DISCOVERY IN ({ids_sql})
    """

    query_bq(sql)

    return {
        "status": "ok",
        "manual": len(discovery_ids),
    }

# ============================================================
# MANUAL DISCOVERY LIST
# ============================================================

def list_manual_discovery():

    sql = f"""
        SELECT
            d.ID_DISCOVERY,
            d.SOURCE_ID,

            s.NAME AS SOURCE_NAME,

            d.URL,
            d.TITLE,
            d.DATE_FOUND

        FROM `{TABLE_DISCOVERY}` d

        LEFT JOIN `{TABLE_SOURCE}` s
          ON d.SOURCE_ID = s.SOURCE_ID

        WHERE d.STATUS = 'MANUAL_REVIEW'

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
            "date_found": r.get(
                "DATE_FOUND"
            ),
        }
        for r in rows
    ]
