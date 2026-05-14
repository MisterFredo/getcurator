import re
from typing import Dict, List, Optional

from config import BQ_PROJECT, BQ_DATASET

from utils.bigquery_utils import (
    query_bq,
)

# ============================================================
# TABLES
# ============================================================

TABLE_COMPANY_ALIAS = (
    f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_COMPANY_ALIAS"
)

TABLE_SOLUTION_ALIAS = (
    f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_SOLUTION_ALIAS"
)

TABLE_ALIAS_REJECTED = (
    f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_ALIAS_REJECTED"
)

# ============================================================
# NORMALIZE
# ============================================================

def normalize(text: Optional[str]) -> str:

    if not text:
        return ""

    text = text.upper()

    text = re.sub(r"\(.*?\)", "", text)

    text = text.replace("+", " PLUS ")

    text = re.sub(r"[^A-Z0-9 ]", " ", text)

    text = re.sub(r"\s+", " ", text)

    return text.strip()

# ============================================================
# COMPANY ALIAS MAP
# ============================================================

def get_company_alias_map() -> Dict:

    rows = query_bq(
        f"""
        SELECT
            ALIAS,
            ID_COMPANY

        FROM `{TABLE_COMPANY_ALIAS}`

        WHERE ID_COMPANY IS NOT NULL
        """
    )

    output = {}

    for row in rows:

        alias = normalize(
            row.get("ALIAS")
        )

        if not alias:
            continue

        output[alias] = {
            "id_company": row.get("ID_COMPANY"),
            "raw_alias": row.get("ALIAS"),
        }

    return output

# ============================================================
# SOLUTION ALIAS MAP
# ============================================================

def get_solution_alias_map() -> Dict:

    rows = query_bq(
        f"""
        SELECT
            ALIAS,
            ID_SOLUTION

        FROM `{TABLE_SOLUTION_ALIAS}`

        WHERE ID_SOLUTION IS NOT NULL
        """
    )

    output = {}

    for row in rows:

        alias = normalize(
            row.get("ALIAS")
        )

        if not alias:
            continue

        output[alias] = {
            "id_solution": row.get("ID_SOLUTION"),
            "raw_alias": row.get("ALIAS"),
        }

    return output

# ============================================================
# RESOLVE COMPANY
# ============================================================

def resolve_company(
    raw_value: str,
    alias_map: Optional[Dict] = None,
):

    if not raw_value:
        return None

    if alias_map is None:
        alias_map = get_company_alias_map()

    normalized = normalize(raw_value)

    return alias_map.get(normalized)

# ============================================================
# RESOLVE SOLUTION
# ============================================================

def resolve_solution(
    raw_value: str,
    alias_map: Optional[Dict] = None,
):

    if not raw_value:
        return None

    if alias_map is None:
        alias_map = get_solution_alias_map()

    normalized = normalize(raw_value)

    return alias_map.get(normalized)

# ============================================================
# INSERT REJECTED ALIAS
# ============================================================

def insert_rejected_alias(
    alias: str,
    entity_type: str,
):

    if not alias:
        return

    normalized = normalize(alias)

    existing = query_bq(
        f"""
        SELECT 1

        FROM `{TABLE_ALIAS_REJECTED}`

        WHERE NORMALIZED_ALIAS = @normalized

        LIMIT 1
        """,
        {
            "normalized": normalized,
        }
    )

    if existing:
        return

    query_bq(
        f"""
        INSERT INTO `{TABLE_ALIAS_REJECTED}` (
            ID_REJECTED,
            RAW_ALIAS,
            NORMALIZED_ALIAS,
            ENTITY_TYPE,
            CREATED_AT
        )

        VALUES (
            GENERATE_UUID(),
            @raw_alias,
            @normalized_alias,
            @entity_type,
            CURRENT_TIMESTAMP()
        )
        """,
        {
            "raw_alias": alias,
            "normalized_alias": normalized,
            "entity_type": entity_type,
        }
    )

# ============================================================
# RESOLVE ENTITIES
# ============================================================

def resolve_entities(
    raw_values: List[str],
):

    company_map = get_company_alias_map()

    solution_map = get_solution_alias_map()

    companies = []
    solutions = []
    unmatched = []

    seen_companies = set()
    seen_solutions = set()
    seen_unmatched = set()

    for raw in raw_values:

        if not raw:
            continue

        normalized = normalize(raw)

        if not normalized:
            continue

        company = resolve_company(
            raw,
            company_map,
        )

        if company:

            id_company = company["id_company"]

            if id_company not in seen_companies:

                companies.append({
                    "raw": raw,
                    "normalized": normalized,
                    "id_company": id_company,
                })

                seen_companies.add(
                    id_company
                )

            continue

        solution = resolve_solution(
            raw,
            solution_map,
        )

        if solution:

            id_solution = solution["id_solution"]

            if id_solution not in seen_solutions:

                solutions.append({
                    "raw": raw,
                    "normalized": normalized,
                    "id_solution": id_solution,
                })

                seen_solutions.add(
                    id_solution
                )

            continue

        if normalized not in seen_unmatched:

            unmatched.append({
                "raw": raw,
                "normalized": normalized,
            })

            seen_unmatched.add(
                normalized
            )

    return {
        "companies": companies,
        "solutions": solutions,
        "unmatched": unmatched,
    }
