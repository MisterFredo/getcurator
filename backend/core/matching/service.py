from typing import List, Dict, Optional

from google.cloud import bigquery

from config import BQ_PROJECT, BQ_DATASET

from utils.bigquery_utils import (
    query_bq,
    get_bigquery_client,
)

from core.matching.resolver import (
    normalize,
    insert_rejected_alias,
    TABLE_ALIAS_REJECTED,
)

# ============================================================
# TABLES
# ============================================================

TABLE_CONTENT = (
    f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_CONTENT"
)

TABLE_COMPANY = (
    f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_COMPANY"
)

TABLE_SOLUTION = (
    f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_SOLUTION"
)

TABLE_COMPANY_ALIAS = (
    f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_COMPANY_ALIAS"
)

TABLE_SOLUTION_ALIAS = (
    f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_SOLUTION_ALIAS"
)

# ============================================================
# FIND MATCH
# ============================================================

def find_match(
    name: str,
    company_map: Dict,
    solution_map: Dict,
):

    norm = normalize(name)

    if norm in company_map:

        return {
            "type_hint": "company",
            "suggested_id": company_map[norm]["id"],
            "suggested_label": company_map[norm]["label"],
        }

    if norm in solution_map:

        return {
            "type_hint": "solution",
            "suggested_id": solution_map[norm]["id"],
            "suggested_label": solution_map[norm]["label"],
        }

    return {
        "type_hint": "unknown",
        "suggested_id": None,
        "suggested_label": None,
    }

# ============================================================
# LIST UNMATCHED ENTITIES
# ============================================================

def list_unmatched_entities() -> List[Dict]:

    # =====================================================
    # FETCH RAW
    # =====================================================

    sql = f"""
    SELECT
        entity,
        COUNT(*) AS count

    FROM `{TABLE_CONTENT}`,
    UNNEST(
        ARRAY_CONCAT(
            IFNULL(SOLUTIONS_LLM, []),
            IFNULL(ACTEURS_CITES, [])
        )
    ) AS entity

    WHERE entity IS NOT NULL
    AND TRIM(entity) != ""

    GROUP BY entity

    ORDER BY count DESC
    """

    rows = query_bq(sql)

    client = get_bigquery_client()

    # =====================================================
    # ALREADY MATCHED / REJECTED
    # =====================================================

    alias_query = f"""
    SELECT ALIAS
    FROM `{TABLE_COMPANY_ALIAS}`

    UNION DISTINCT

    SELECT ALIAS
    FROM `{TABLE_SOLUTION_ALIAS}`

    UNION DISTINCT

    SELECT ALIAS
    FROM `{TABLE_ALIAS_REJECTED}`
    """

    alias_rows = client.query(
        alias_query
    ).result()

    alias_set = {
        normalize(row["ALIAS"])
        for row in alias_rows
        if row["ALIAS"]
    }

    # =====================================================
    # LOAD COMPANIES
    # =====================================================

    company_rows = client.query(f"""
        SELECT
            ID_COMPANY,
            NAME

        FROM `{TABLE_COMPANY}`
    """).result()

    company_map = {
        normalize(r["NAME"]): {
            "id": r["ID_COMPANY"],
            "label": r["NAME"],
        }
        for r in company_rows
        if r["NAME"]
    }

    # =====================================================
    # LOAD SOLUTIONS
    # =====================================================

    solution_rows = client.query(f"""
        SELECT
            ID_SOLUTION,
            NAME

        FROM `{TABLE_SOLUTION}`
    """).result()

    solution_map = {
        normalize(r["NAME"]): {
            "id": r["ID_SOLUTION"],
            "label": r["NAME"],
        }
        for r in solution_rows
        if r["NAME"]
    }

    # =====================================================
    # BUILD RESULTS
    # =====================================================

    results = []

    seen = set()

    for r in rows:

        raw = r["entity"]

        if not raw:
            continue

        norm = normalize(raw)

        # =================================================
        # ALREADY TREATED
        # =================================================

        if norm in alias_set:
            continue

        # =================================================
        # DEDUP
        # =================================================

        if norm in seen:
            continue

        seen.add(norm)

        # =================================================
        # FIND MATCH
        # =================================================

        match = find_match(
            raw,
            company_map,
            solution_map,
        )

        results.append({
            "value": raw,
            "count": r["count"],
            "type_hint": match["type_hint"],
            "suggested_id": match["suggested_id"],
            "suggested_label": match["suggested_label"],
        })

    # =====================================================
    # SORT
    # =====================================================

    results.sort(
        key=lambda x: (
            -x["count"],
            x["value"].upper(),
        )
    )

    return results

# ============================================================
# MATCH ENTITY
# ============================================================

def match_entity(
    alias: str,
    target_type: str,
    target_id: Optional[str] = None,
):

    client = get_bigquery_client()

    alias = alias.strip()

    if not alias:
        raise ValueError("alias vide")

    # =====================================================
    # NORMALIZATION SQL
    # =====================================================

    def norm_expr(field: str) -> str:

        return f"""
        REGEXP_REPLACE(
            UPPER({field}),
            r'[^A-Z0-9 ]',
            ''
        )
        """

    # =====================================================
    # IGNORE
    # =====================================================

    if target_type == "ignore":

        insert_rejected_alias(
            alias=alias,
            entity_type="unknown",
        )

        return {
            "status": "ignored",
            "alias": alias,
        }

    # =====================================================
    # COMPANY
    # =====================================================

    if target_type == "company":

        if not target_id:
            raise ValueError(
                "target_id obligatoire"
            )

        sql_alias = f"""
        INSERT INTO `{TABLE_COMPANY_ALIAS}` (
            ALIAS,
            ID_COMPANY
        )

        SELECT
            @alias,
            @target_id

        FROM UNNEST([1]) AS _

        WHERE NOT EXISTS (

            SELECT 1

            FROM `{TABLE_COMPANY_ALIAS}`

            WHERE
                {norm_expr("ALIAS")}
                =
                {norm_expr("CAST(@alias AS STRING)")}
        )
        """

        client.query(
            sql_alias,
            job_config=bigquery.QueryJobConfig(
                query_parameters=[
                    bigquery.ScalarQueryParameter(
                        "alias",
                        "STRING",
                        alias,
                    ),
                    bigquery.ScalarQueryParameter(
                        "target_id",
                        "STRING",
                        target_id,
                    ),
                ]
            ),
        ).result()

        print(
            "✅ ENTITY MATCHED TO COMPANY:",
            {
                "alias": alias,
                "id_company": target_id,
            }
        )

        return {
            "status": "matched",
            "target_type": "company",
        }

    # =====================================================
    # SOLUTION
    # =====================================================

    if target_type == "solution":

        if not target_id:
            raise ValueError(
                "target_id obligatoire"
            )

        sql_alias = f"""
        INSERT INTO `{TABLE_SOLUTION_ALIAS}` (
            ALIAS,
            ID_SOLUTION
        )

        SELECT
            @alias,
            @target_id

        FROM UNNEST([1]) AS _

        WHERE NOT EXISTS (

            SELECT 1

            FROM `{TABLE_SOLUTION_ALIAS}`

            WHERE
                {norm_expr("ALIAS")}
                =
                {norm_expr("CAST(@alias AS STRING)")}
        )
        """

        client.query(
            sql_alias,
            job_config=bigquery.QueryJobConfig(
                query_parameters=[
                    bigquery.ScalarQueryParameter(
                        "alias",
                        "STRING",
                        alias,
                    ),
                    bigquery.ScalarQueryParameter(
                        "target_id",
                        "STRING",
                        target_id,
                    ),
                ]
            ),
        ).result()

        print(
            "✅ ENTITY MATCHED TO SOLUTION:",
            {
                "alias": alias,
                "id_solution": target_id,
            }
        )

        return {
            "status": "matched",
            "target_type": "solution",
        }

    # =====================================================
    # UNKNOWN TYPE
    # =====================================================

    raise ValueError(
        f"target_type inconnu: {target_type}"
    )
