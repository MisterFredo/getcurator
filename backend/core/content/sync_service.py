from datetime import datetime, timezone
from typing import List, Dict, Optional

from config import BQ_PROJECT, BQ_DATASET

from utils.bigquery_utils import query_bq

from core.numbers.service import (
    get_numbers_from_content,
)

from core.numbers.backlog_llm import (
    process_backlog_row,
)

from core.numbers.backlog_insert_service import (
    insert_backlog_batch,
)

# ============================================================
# TABLES
# ============================================================

TABLE_CONTENT = f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_CONTENT"

TABLE_CONTENT_ENRICHED = (
    f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_CONTENT_ENRICHED"
)

TABLE_CONTENT_COMPANY = (
    f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_CONTENT_COMPANY"
)

TABLE_CONTENT_SOLUTION = (
    f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_CONTENT_SOLUTION"
)

TABLE_COMPANY_ALIAS = (
    f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_COMPANY_ALIAS"
)

TABLE_SOLUTION_ALIAS = (
    f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_SOLUTION_ALIAS"
)

# ============================================================
# COMPANY MATCHING
# ============================================================

def sync_content_companies(id_content: str):

    query_bq(
        f"""
        DELETE FROM `{TABLE_CONTENT_COMPANY}`
        WHERE ID_CONTENT = @id_content
        """,
        {
            "id_content": id_content,
        }
    )

    query_bq(
        f"""
        INSERT INTO `{TABLE_CONTENT_COMPANY}` (
            ID_CONTENT,
            ID_COMPANY
        )

        SELECT DISTINCT
            c.ID_CONTENT,
            a.ID_COMPANY

        FROM `{TABLE_CONTENT}` c,
        UNNEST(c.ACTEURS_CITES) AS raw

        JOIN `{TABLE_COMPANY_ALIAS}` a
            ON REGEXP_REPLACE(
                UPPER(TRIM(raw)),
                r'[^A-Z0-9 ]',
                ''
            )
            =
            REGEXP_REPLACE(
                UPPER(TRIM(a.ALIAS)),
                r'[^A-Z0-9 ]',
                ''
            )

        WHERE
            c.ID_CONTENT = @id_content
            AND a.MATCH_STATUS = 'MATCH'
            AND raw IS NOT NULL
            AND TRIM(raw) != ''
        """,
        {
            "id_content": id_content,
        }
    )

    print(
        "✅ COMPANY SYNC DONE:",
        id_content,
    )

# ============================================================
# SOLUTION MATCHING
# ============================================================

def sync_content_solutions(id_content: str):

    query_bq(
        f"""
        DELETE FROM `{TABLE_CONTENT_SOLUTION}`
        WHERE ID_CONTENT = @id_content
        """,
        {
            "id_content": id_content,
        }
    )

    query_bq(
        f"""
        INSERT INTO `{TABLE_CONTENT_SOLUTION}` (
            ID_CONTENT,
            ID_SOLUTION
        )

        SELECT DISTINCT
            c.ID_CONTENT,
            a.ID_SOLUTION

        FROM `{TABLE_CONTENT}` c,
        UNNEST(
            ARRAY_CONCAT(
                IFNULL(c.SOLUTIONS_LLM, []),
                IFNULL(c.ACTEURS_CITES, [])
            )
        ) AS raw

        JOIN `{TABLE_SOLUTION_ALIAS}` a
            ON REGEXP_REPLACE(
                UPPER(TRIM(raw)),
                r'[^A-Z0-9 ]',
                ''
            )
            =
            REGEXP_REPLACE(
                UPPER(TRIM(a.ALIAS)),
                r'[^A-Z0-9 ]',
                ''
            )

        WHERE
            c.ID_CONTENT = @id_content
            AND a.MATCH_STATUS = 'MATCH'
            AND raw IS NOT NULL
            AND TRIM(raw) != ''
        """,
        {
            "id_content": id_content,
        }
    )

    print(
        "✅ SOLUTION SYNC DONE:",
        id_content,
    )

# ============================================================
# SYNC ALL NUMBERS
# ============================================================

def sync_all_numbers():

    print(
        "🚀 GLOBAL NUMBERS SYNC START"
    )

    # ========================================================
    # FETCH PUBLISHED CONTENTS
    # ========================================================

    rows = query_bq(
        f"""
        SELECT ID_CONTENT

        FROM `{TABLE_CONTENT}`

        WHERE STATUS = 'PUBLISHED'
        """
    )

    if not rows:

        return {
            "total": 0,
            "synced": 0,
            "errors": 0,
            "results": [],
        }

    results = []

    # ========================================================
    # LOOP
    # ========================================================

    for row in rows:

        id_content = row["ID_CONTENT"]

        try:

            result = sync_content_numbers(
                id_content=id_content,
            )

            results.append({
                "id_content": id_content,
                "status": "ok",
                **result,
            })

        except Exception as e:

            results.append({
                "id_content": id_content,
                "status": "error",
                "error": str(e),
            })

    # ========================================================
    # SUMMARY
    # ========================================================

    synced_count = len([
        r for r in results
        if r["status"] == "ok"
    ])

    error_count = len([
        r for r in results
        if r["status"] == "error"
    ])

    output = {
        "total": len(rows),
        "synced": synced_count,
        "errors": error_count,
        "results": results,
    }

    print(
        "✅ GLOBAL NUMBERS SYNC DONE:",
        output,
    )

    return output

# ============================================================
# REBUILD ENRICHED ROW
# ============================================================

def rebuild_content_enriched_row(id_content: str):

    query_bq(
        f"""
        DELETE FROM `{TABLE_CONTENT_ENRICHED}`
        WHERE id_content = @id_content
        """,
        {
            "id_content": id_content,
        }
    )

    query_bq(
        f"""
        INSERT INTO `{TABLE_CONTENT_ENRICHED}` (
            id_content,
            source_id,
            title,
            excerpt,
            content_body,
            signal_analytique,
            mecanique_expliquee,
            enjeu_strategique,
            point_de_friction,
            chiffres,
            acteurs_cites,
            concepts_llm,
            solutions_llm,
            topics_llm,
            status,
            is_active,
            source_date,
            published_at,
            created_at,
            updated_at,
            universes,
            topics,
            companies,
            solutions,
            concepts,
            content_type,
            id_primary_company
        )

        SELECT
            c.ID_CONTENT AS id_content,
            c.SOURCE_ID AS source_id,
            c.TITLE AS title,
            c.EXCERPT AS excerpt,
            c.CONTENT_BODY AS content_body,
            c.SIGNAL_ANALYTIQUE AS signal_analytique,
            c.MECANIQUE_EXPLIQUEE AS mecanique_expliquee,
            c.ENJEU_STRATEGIQUE AS enjeu_strategique,
            c.POINT_DE_FRICTION AS point_de_friction,
            c.CHIFFRES AS chiffres,
            c.ACTEURS_CITES AS acteurs_cites,
            c.CONCEPTS_LLM AS concepts_llm,
            c.SOLUTIONS_LLM AS solutions_llm,
            c.TOPICS_LLM AS topics_llm,
            c.STATUS AS status,
            c.IS_ACTIVE AS is_active,
            c.SOURCE_DATE AS source_date,
            c.PUBLISHED_AT AS published_at,
            c.CREATED_AT AS created_at,
            c.UPDATED_AT AS updated_at,

            -- ====================================================
            -- UNIVERSes (🔥 SOURCE BASED)
            -- ====================================================

            ARRAY(
                SELECT DISTINCT AS STRUCT
                    u.ID_UNIVERSE AS id_universe,
                    u.LABEL AS label

                FROM `{BQ_PROJECT}.{BQ_DATASET}.RATECARD_SOURCE_UNIVERSE` su

                JOIN `{BQ_PROJECT}.{BQ_DATASET}.RATECARD_UNIVERSE` u
                    ON su.ID_UNIVERSE = u.ID_UNIVERSE

                WHERE su.ID_SOURCE = c.SOURCE_ID
            ) AS universes,

            -- ====================================================
            -- TOPICS
            -- ====================================================

            ARRAY(
                SELECT DISTINCT AS STRUCT
                    t.ID_TOPIC AS id_topic,
                    t.LABEL AS label,
                    t.TOPIC_AXIS AS topic_axis

                FROM `{BQ_PROJECT}.{BQ_DATASET}.RATECARD_CONTENT_TOPIC` ct

                JOIN `{BQ_PROJECT}.{BQ_DATASET}.RATECARD_TOPIC` t
                    ON ct.ID_TOPIC = t.ID_TOPIC

                WHERE ct.ID_CONTENT = c.ID_CONTENT
            ) AS topics,

            -- ====================================================
            -- COMPANIES
            -- ====================================================

            ARRAY(
                SELECT DISTINCT AS STRUCT
                    co.ID_COMPANY AS id_company,
                    co.NAME AS name,
                    co.MEDIA_LOGO_RECTANGLE_ID AS media_logo_rectangle_id

                FROM `{TABLE_CONTENT_COMPANY}` cc

                JOIN `{BQ_PROJECT}.{BQ_DATASET}.RATECARD_COMPANY` co
                    ON cc.ID_COMPANY = co.ID_COMPANY

                WHERE cc.ID_CONTENT = c.ID_CONTENT
            ) AS companies,

            -- ====================================================
            -- SOLUTIONS
            -- ====================================================

            ARRAY(
                SELECT DISTINCT AS STRUCT
                    s.ID_SOLUTION AS id_solution,
                    s.NAME AS name

                FROM `{TABLE_CONTENT_SOLUTION}` cs

                JOIN `{BQ_PROJECT}.{BQ_DATASET}.RATECARD_SOLUTION` s
                    ON cs.ID_SOLUTION = s.ID_SOLUTION

                WHERE cs.ID_CONTENT = c.ID_CONTENT
            ) AS solutions,

            -- ====================================================
            -- CONCEPTS
            -- ====================================================

            ARRAY(
                SELECT DISTINCT AS STRUCT
                    cp.ID_CONCEPT AS id_concept,
                    cpt.LABEL AS label

                FROM `{BQ_PROJECT}.{BQ_DATASET}.RATECARD_CONTENT_CONCEPT` cp

                JOIN `{BQ_PROJECT}.{BQ_DATASET}.RATECARD_CONCEPT` cpt
                    ON cp.ID_CONCEPT = cpt.ID_CONCEPT

                WHERE cp.ID_CONTENT = c.ID_CONTENT
            ) AS concepts,

            LOWER(
                COALESCE(
                    c.CONTENT_TYPE,
                    'ANALYSIS'
                )
            ) AS content_type,

            c.ID_PRIMARY_COMPANY AS id_primary_company

        FROM `{TABLE_CONTENT}` c

        WHERE
            c.ID_CONTENT = @id_content
            AND c.STATUS = 'PUBLISHED'
        """,
        {
            "id_content": id_content,
        }
    )

    print(
        "✅ CONTENT_ENRICHED REBUILT:",
        id_content,
    )
# ============================================================
# NUMBERS BACKLOG
# ============================================================

def sync_content_numbers(id_content: str):

    print(
        "📊 NUMBERS SYNC START:",
        id_content,
    )

    backlog_rows = get_numbers_from_content(
        id_content
    )

    if not backlog_rows:

        print(
            "ℹ️ No valid numbers found:",
            id_content,
        )

        return {
            "id_content": id_content,
            "numbers_found": 0,
            "numbers_inserted": 0,
        }

    processed_results = []

    for backlog_row in backlog_rows:

        result = process_backlog_row(
            backlog_row
        )

        if result.get("status") == "ok":

            processed_results.append(
                result
            )

    if processed_results:

        insert_backlog_batch(
            processed_results
        )

        print(
            f"✅ {len(processed_results)} backlog numbers inserted:",
            id_content,
        )

    else:

        print(
            "ℹ️ No valid backlog results:",
            id_content,
        )

    return {
        "id_content": id_content,
        "numbers_found": len(backlog_rows),
        "numbers_inserted": len(processed_results),
    }


# ============================================================
# FULL CONTENT SYNC
# ============================================================

def sync_content(
    id_content: str,
    sync_numbers: bool = False,
):

    started_at = datetime.now(
        timezone.utc
    )

    print(
        "🚀 CONTENT SYNC START:",
        id_content,
    )

    sync_content_companies(
        id_content=id_content,
    )

    sync_content_solutions(
        id_content=id_content,
    )

    rebuild_content_enriched_row(
        id_content=id_content,
    )

    numbers_result = None

    if sync_numbers:

        numbers_result = sync_content_numbers(
            id_content=id_content,
        )

    duration = (
        datetime.now(timezone.utc)
        - started_at
    ).total_seconds()

    result = {
        "id_content": id_content,
        "companies_synced": True,
        "solutions_synced": True,
        "enriched_rebuilt": True,
        "numbers_synced": sync_numbers,
        "numbers_result": numbers_result,
        "duration_seconds": duration,
    }

    print(
        "✅ CONTENT SYNC DONE:",
        result,
    )

    return result

# ============================================================
# BULK SYNC CONTENTS
# ============================================================

def bulk_sync_contents(ids: list[str]):

    results = []

    for id_content in ids:

        try:

            result = sync_content(
                id_content=id_content,
            )

            results.append({
                "id_content": id_content,
                "status": "ok",
                **result,
            })

        except Exception as e:

            results.append({
                "id_content": id_content,
                "status": "error",
                "error": str(e),
            })

    return {
        "total": len(ids),
        "synced": len([
            r for r in results
            if r["status"] == "ok"
        ]),
        "errors": len([
            r for r in results
            if r["status"] == "error"
        ]),
        "results": results,
    }

# ============================================================
# FULL SYNC — ALL PUBLISHED CONTENTS
# ============================================================

def sync_all_published_contents(
    sync_numbers: bool = False,
):

    started_at = datetime.now(
        timezone.utc
    )

    print(
        "🚀 FULL CONTENT SYNC START"
    )

    # ========================================================
    # GET PUBLISHED CONTENTS
    # ========================================================

    rows = query_bq(
        f"""
        SELECT ID_CONTENT
        FROM `{TABLE_CONTENT}`
        WHERE STATUS = 'PUBLISHED'
        ORDER BY PUBLISHED_AT DESC
        """
    )

    ids = [
        r["ID_CONTENT"]
        for r in rows
    ]

    results = []

    # ========================================================
    # LOOP
    # ========================================================

    for id_content in ids:

        try:

            result = sync_content(
                id_content=id_content,
                sync_numbers=sync_numbers,
            )

            results.append({
                "id_content": id_content,
                "status": "ok",
                **result,
            })

        except Exception as e:

            results.append({
                "id_content": id_content,
                "status": "error",
                "error": str(e),
            })

    # ========================================================
    # STATS
    # ========================================================

    synced = len([
        r for r in results
        if r["status"] == "ok"
    ])

    errors = len([
        r for r in results
        if r["status"] == "error"
    ])

    duration = (
        datetime.now(timezone.utc)
        - started_at
    ).total_seconds()

    final_result = {
        "total": len(ids),
        "synced": synced,
        "errors": errors,
        "sync_numbers": sync_numbers,
        "duration_seconds": duration,
        "results": results,
    }

    print(
        "✅ FULL CONTENT SYNC DONE:",
        final_result,
    )

    return final_result

