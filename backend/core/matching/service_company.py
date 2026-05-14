from typing import List, Dict
from google.cloud import bigquery

import re
import uuid
from datetime import datetime

from config import BQ_PROJECT, BQ_DATASET
from utils.bigquery_utils import query_bq, get_bigquery_client

from api.matching.models import (
    CompanyMatch,
    SolutionMatch,
)

from core.matching.service_solution import (
    match_solution,
)

TABLE_CONTENT = f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_CONTENT"

TABLE_ALIAS = (
    f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_COMPANY_ALIAS"
)

TABLE_COMPANY = (
    f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_COMPANY"
)

TABLE_ALIAS_REJECTED = (
    f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_ALIAS_REJECTED"
)

# ===============================================
# NORMALISATION
# ===============================================

def normalize(text: str) -> str:

    if not text:
        return ""

    text = text.upper()

    text = re.sub(r"\(.*?\)", "", text)

    text = re.sub(r"[^A-Z0-9 ]", " ", text)

    text = re.sub(r"\s+", " ", text)

    return text.strip()

# ===============================================
# FIND MATCH
# ===============================================

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
            "suggested_label": company_map[norm]["label"]
        }

    if norm in solution_map:

        return {
            "type_hint": "solution",
            "suggested_id": solution_map[norm]["id"],
            "suggested_label": solution_map[norm]["label"]
        }

    return {
        "type_hint": "unknown",
        "suggested_id": None,
        "suggested_label": None
    }

# ===============================================
# LIST UNMATCHED COMPANIES
# ===============================================

def list_unmatched_companies() -> List[Dict]:

    # =====================================================
    # FETCH RAW (ACTEURS)
    # =====================================================

    sql = f"""
    SELECT
        company,
        COUNT(*) AS count

    FROM `{TABLE_CONTENT}`,
    UNNEST(ACTEURS_CITES) AS company

    WHERE company IS NOT NULL
    AND TRIM(company) != ""

    GROUP BY company
    """

    rows = query_bq(sql)

    client = get_bigquery_client()

    # =====================================================
    # ALIAS DÉJÀ MATCHÉS
    # =====================================================

    alias_query = f"""
    SELECT ALIAS
    FROM `{TABLE_ALIAS}`
    """

    alias_rows = client.query(alias_query).result()

    alias_set = {
        normalize(row["ALIAS"])
        for row in alias_rows
        if row["ALIAS"]
    }

    # =====================================================
    # LOAD COMPANIES
    # =====================================================

    company_rows = client.query(f"""
        SELECT ID_COMPANY, NAME
        FROM `{TABLE_COMPANY}`
    """).result()

    company_map = {
        normalize(r["NAME"]): {
            "id": r["ID_COMPANY"],
            "label": r["NAME"]
        }
        for r in company_rows
        if r["NAME"]
    }

    company_set = set(company_map.keys())

    # =====================================================
    # LOAD SOLUTIONS
    # =====================================================

    solution_rows = client.query(f"""
        SELECT ID_SOLUTION, NAME
        FROM `{BQ_PROJECT}.{BQ_DATASET}.RATECARD_SOLUTION`
    """).result()

    solution_map = {
        normalize(r["NAME"]): {
            "id": r["ID_SOLUTION"],
            "label": r["NAME"]
        }
        for r in solution_rows
        if r["NAME"]
    }

    solution_set = set(solution_map.keys())

    # =====================================================
    # BUILD RESULTS
    # =====================================================

    results = []

    seen = set()

    for r in rows:

        raw = r["company"]

        if not raw:
            continue

        norm = normalize(raw)

        # 🔴 déjà traité
        if norm in alias_set:
            continue

        # 🔴 dédup
        if norm in seen:
            continue

        seen.add(norm)

        match = find_match(
            norm,
            company_map,
            solution_map,
        )

        # 🔴 déjà company existante
        if norm in company_set:
            continue

        # 🔴 déjà solution existante
        if norm in solution_set:
            continue

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
            x["value"].upper()
        )
    )

    return results

# ===============================================
# INSERT REJECTED
# ===============================================

def insert_rejected_alias(
    alias: str,
    entity_type: str,
):

    client = get_bigquery_client()

    query = f"""
    MERGE `{TABLE_ALIAS_REJECTED}` t

    USING (
        SELECT
            @alias AS ALIAS,
            @entity_type AS ENTITY_TYPE
    ) s

    ON
        REGEXP_REPLACE(
            UPPER(TRIM(t.ALIAS)),
            r'[^A-Z0-9 ]',
            ''
        )
        =
        REGEXP_REPLACE(
            UPPER(TRIM(s.ALIAS)),
            r'[^A-Z0-9 ]',
            ''
        )

    WHEN MATCHED THEN
        UPDATE SET
            LAST_SEEN_AT = CURRENT_TIMESTAMP(),
            NB_OCCURRENCES = COALESCE(t.NB_OCCURRENCES, 1) + 1

    WHEN NOT MATCHED THEN
        INSERT (
            ID_REJECTED,
            ALIAS,
            ENTITY_TYPE,
            FIRST_SEEN_AT,
            LAST_SEEN_AT,
            NB_OCCURRENCES
        )
        VALUES (
            @id_rejected,
            s.ALIAS,
            s.ENTITY_TYPE,
            CURRENT_TIMESTAMP(),
            CURRENT_TIMESTAMP(),
            1
        )
    """

    client.query(
        query,
        job_config=bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter(
                    "alias",
                    "STRING",
                    alias
                ),
                bigquery.ScalarQueryParameter(
                    "entity_type",
                    "STRING",
                    entity_type
                ),
                bigquery.ScalarQueryParameter(
                    "id_rejected",
                    "STRING",
                    str(uuid.uuid4())
                ),
            ]
        ),
    ).result()

# ===============================================
# MATCH COMPANY
# ===============================================

def match_company(data: CompanyMatch):

    client = get_bigquery_client()

    alias = data.alias.strip()

    if not alias:
        raise ValueError("alias vide")

    def norm_expr(field: str) -> str:

        return f"""
        REGEXP_REPLACE(
            UPPER({field}),
            r'[^A-Z0-9 ]',
            ''
        )
        """

    # =====================================================
    # FALLBACK SOLUTION AUTO
    # =====================================================

    fallback_sql = f"""
    SELECT ID_SOLUTION

    FROM `{BQ_PROJECT}.{BQ_DATASET}.RATECARD_SOLUTION`

    WHERE
        {norm_expr("NAME")}
        =
        {norm_expr("CAST(@alias AS STRING)")}

    LIMIT 1
    """

    fallback_job = client.query(
        fallback_sql,
        job_config=bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter(
                    "alias",
                    "STRING",
                    alias
                ),
            ]
        ),
    )

    fallback_rows = list(
        fallback_job.result()
    )

    if fallback_rows and not data.id_company:

        solution_id = fallback_rows[0]["ID_SOLUTION"]

        match_solution(
            SolutionMatch(
                alias=alias,
                id_solution=solution_id,
                action="MATCH"
            )
        )

        return

    # =====================================================
    # IGNORE
    # =====================================================

    if data.action == "IGNORE":

        insert_rejected_alias(
            alias=alias,
            entity_type="company",
        )

        return

    # =====================================================
    # MATCH
    # =====================================================

    if data.action != "MATCH":
        raise ValueError("Action inconnue")

    if not data.id_company:
        raise ValueError("id_company obligatoire")

    sql_alias = f"""
    INSERT INTO `{TABLE_ALIAS}` (
        ALIAS,
        ID_COMPANY
    )

    SELECT
        @alias,
        @id_company

    FROM UNNEST([1]) AS _

    WHERE NOT EXISTS (

        SELECT 1

        FROM `{TABLE_ALIAS}`

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
                    alias
                ),
                bigquery.ScalarQueryParameter(
                    "id_company",
                    "STRING",
                    data.id_company
                ),
            ]
        ),
    ).result()

    print(
        "✅ COMPANY MATCHED:",
        {
            "alias": alias,
            "id_company": data.id_company,
        }
    )
