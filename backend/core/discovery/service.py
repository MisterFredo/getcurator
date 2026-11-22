from typing import List, Dict
from datetime import datetime
import re
import uuid
import time
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

# ============================================================
# INSERT DISCOVERY URLS
# ============================================================

def insert_discovery_urls(
    items: list[dict],
):

    if not items:
        return 0

    client = get_bigquery_client()

    now = datetime.utcnow().isoformat()

    payload = []

    for item in items:

        payload.append(
            {
                "ID_DISCOVERY": str(
                    uuid.uuid4()
                ),
                "SOURCE_ID": item[
                    "source_id"
                ],
                "URL": item[
                    "url"
                ],
                "TITLE": item.get(
                    "title"
                ),
                "STATUS": "NEW",
                "DATE_FOUND": now,
                "CREATED_AT": now,
            }
        )

    client.load_table_from_json(
        payload,
        TABLE_DISCOVERY,
        job_config=bigquery.LoadJobConfig(
            write_disposition="WRITE_APPEND"
        ),
    ).result()

    return len(
        payload
    )


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

    # ========================================================
    # DISCOVER
    # ========================================================

    if source.get("ACQUISITION_MODE") == "LINKEDIN_BRIGHTDATA":
        from core.discovery.linkedin_brightdata_service import scan
        return scan(source_id, start=True)

    urls = discover_urls(
        source
    )

    # ========================================================
    # EXISTING URLS
    # Charge une seule fois les URLs existantes
    # ========================================================

    existing_discovery = (
        get_existing_discovery_urls()
    )

    existing_raw = (
        get_existing_raw_urls()
    )

    # ========================================================
    # FILTER NEW URLS IN MEMORY
    # ========================================================

    new_items = []

    for item in urls:

        url = item[
            "url"
        ]

        if url in existing_discovery:
            continue

        if url in existing_raw:
            continue

        new_items.append(
            {
                "source_id": source_id,
                "url": url,
                "title": item.get(
                    "title"
                ),
            }
        )

        # évite les doublons
        # dans le même scan
        existing_discovery.add(
            url
        )

    # ========================================================
    # BATCH INSERT
    # ========================================================

    if new_items:

        insert_discovery_urls(
            new_items
        )

    # ========================================================
    # RESULT
    # ========================================================

    return {
        "status": "ok",
        "scanned_sources": 1,
        "discovered_urls": len(
            new_items
        ),
    }

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
          AND s.ACQUISITION_MODE NOT IN ('MANUAL','PDF_MANUAL','LINKEDIN_PROFILE','NEWSLETTER_MANUAL','LINKEDIN_BRIGHTDATA')
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

TABLE_NO_GO_RULES = f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_DISCOVERY_NO_GO_RULE"


def list_no_go_rules(active_only: bool = False):
    where = "WHERE IS_ACTIVE" if active_only else ""
    rows = query_bq(f"""
        SELECT ID_RULE, EXPRESSION, REASON, IS_ACTIVE, COALESCE(RULE_TYPE, 'NO_GO') AS RULE_TYPE
        FROM `{TABLE_NO_GO_RULES}`
        {where}
        ORDER BY LENGTH(EXPRESSION) DESC, EXPRESSION, ID_RULE
    """)
    return [
        {
            "id_rule": row["ID_RULE"],
            "expression": row["EXPRESSION"],
            "reason": row["REASON"],
            "is_active": row["IS_ACTIVE"],
            "rule_type": row["RULE_TYPE"],
        }
        for row in rows
    ]


def save_no_go_rule(rule_id, expression: str, reason: str, is_active: bool, rule_type: str = "NO_GO"):
    expression = " ".join(expression.split())
    reason = reason.strip()
    if not expression or not reason:
        raise ValueError("L’expression et le motif sont obligatoires.")

    expression_key = expression.casefold()
    creating = rule_id is None
    if creating:
        rule_id = uuid.uuid4()

    query_bq(f"""
        ASSERT @creating = 'true' OR NOT EXISTS (
            SELECT 1 FROM `{TABLE_NO_GO_RULES}`
            WHERE EXPRESSION_KEY = @expression_key AND ID_RULE != @rule_id
        ) AS 'Cette expression existe déjà.';

        MERGE `{TABLE_NO_GO_RULES}` AS target
        USING (SELECT @rule_id AS ID_RULE) AS source
        ON (@creating = 'true' AND target.EXPRESSION_KEY = @expression_key)
           OR (@creating = 'false' AND target.ID_RULE = source.ID_RULE)
        WHEN MATCHED AND @creating = 'false' THEN UPDATE SET
            EXPRESSION = @expression,
            EXPRESSION_KEY = @expression_key,
            REASON = @reason,
            RULE_TYPE = @rule_type,
            IS_ACTIVE = (@active = 'true'),
            UPDATED_AT = CURRENT_TIMESTAMP()
        WHEN NOT MATCHED AND @creating = 'true' THEN
            INSERT (ID_RULE, EXPRESSION, EXPRESSION_KEY, REASON, RULE_TYPE, IS_ACTIVE, UPDATED_AT)
            VALUES (
                @rule_id, @expression, @expression_key, @reason, @rule_type,
                @active = 'true', CURRENT_TIMESTAMP()
            )
    """, {
        "rule_id": str(rule_id),
        "expression": expression,
        "expression_key": expression_key,
        "reason": reason,
        "rule_type": rule_type,
        "active": "true" if is_active else "false",
        "creating": "true" if creating else "false",
    })


def normalize_signal(value: str) -> str:
    return " ".join(value.casefold().split())


def compile_title_signal(value: str) -> re.Pattern:
    return re.compile(r"(?<!\w)" + re.escape(normalize_signal(value)) + r"(?!\w)")


def recommend_title(title, signals):
    normalized_title = normalize_signal(title or "")
    matches = {
        kind: next(
            (reason for pattern, reason in patterns if pattern.search(normalized_title)),
            None,
        )
        for kind, patterns in signals.items()
    }
    go, no_go = matches["GO"], matches["NO_GO"]
    if go and no_go:
        return "TO_CHECK", f"Signaux contradictoires · GO : {go} · NO GO : {no_go}"
    if go:
        return "GO", go
    if no_go:
        return "NO_GO", no_go
    return "TO_CHECK", None


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
            d.PUBLISHED_AT,

            s.NAME AS SOURCE_NAME

        FROM `{TABLE_DISCOVERY}` d

        LEFT JOIN `{TABLE_SOURCE}` s
          ON d.SOURCE_ID = s.SOURCE_ID

        WHERE d.STATUS = 'NEW'

        ORDER BY d.DATE_FOUND DESC
    """

    rows = query_bq(sql)

    if not rows:
        return []

    rules = list_no_go_rules(active_only=True)
    companies = query_bq(f"""
        SELECT DISTINCT TRIM(NAME) AS NAME
        FROM `{BQ_PROJECT}.{BQ_DATASET}.RATECARD_COMPANY`
        WHERE NULLIF(TRIM(NAME), '') IS NOT NULL
        ORDER BY LENGTH(NAME) DESC, NAME
    """)
    signals = {"GO": [], "NO_GO": []}
    for rule in rules:
        signals[rule["rule_type"]].append(
            (compile_title_signal(rule["expression"]), rule["reason"])
        )
    for company in companies:
        name = company["NAME"]
        signals["GO"].append((compile_title_signal(name), f"Société détectée · {name}"))

    items = []
    for r in rows:
        title = r.get("TITLE")
        recommendation, reason = recommend_title(title, signals)
        items.append({
            "id_discovery": r["ID_DISCOVERY"],
            "source_id": r["SOURCE_ID"],
            "source_name": r.get(
                "SOURCE_NAME"
            ),
            "url": r["URL"],
            "title": title,
            "recommendation": recommendation,
            "recommendation_reason": reason,
            "status": r["STATUS"],
            "published_at": r.get("PUBLISHED_AT"),
            "date_found": r.get(
                "DATE_FOUND"
            ),
            "created_at": r.get(
                "CREATED_AT"
            ),
        })
    return items


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

    # IDs are UUIDs from the discovery table; validate before existing SQL interpolation.
    discovery_ids = [str(uuid.UUID(value)) for value in discovery_ids]
    ids_sql = ",".join("'" + value + "'" for value in discovery_ids)

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

    # IDs are UUIDs from the discovery table; validate before existing SQL interpolation.
    discovery_ids = [str(uuid.UUID(value)) for value in discovery_ids]
    ids_sql = ",".join("'" + value + "'" for value in discovery_ids)

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

    from core.discovery.linkedin_brightdata_service import store_discoveries
    cached = query_bq(f"SELECT ID_DISCOVERY FROM `{TABLE_DISCOVERY}` WHERE ID_DISCOVERY IN ({ids_sql}) AND CAPTURE_URI IS NOT NULL")
    cached_ids = {r["ID_DISCOVERY"] for r in cached}
    linked = store_discoveries(list(cached_ids)) if cached_ids else {"stored":0,"skipped":0,"errors":0}
    stored, skipped, errors = linked["stored"], linked["skipped"], linked["errors"]
    rows = [r for r in rows if r["ID_DISCOVERY"] not in cached_ids]

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

        finally:

            # Évite d'enchaîner les requêtes vers
            # les sites trop rapidement.
            time.sleep(3)

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

    # IDs are UUIDs from the discovery table; validate before existing SQL interpolation.
    discovery_ids = [str(uuid.UUID(value)) for value in discovery_ids]
    ids_sql = ",".join("'" + value + "'" for value in discovery_ids)

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
