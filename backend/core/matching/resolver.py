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

def normalize(
    text: Optional[str]
) -> str:

    if not text:
        return ""

    text = text.upper()

    text = re.sub(
        r"\(.*?\)",
        "",
        text
    )

    text = text.replace(
        "+",
        " PLUS "
    )

    text = re.sub(
        r"[^A-Z0-9 ]",
        " ",
        text
    )

    text = re.sub(
        r"\s+",
        " ",
        text
    )

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
            "id_company": row.get(
                "ID_COMPANY"
            ),
            "raw_alias": row.get(
                "ALIAS"
            ),
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
            "id_solution": row.get(
                "ID_SOLUTION"
            ),
            "raw_alias": row.get(
                "ALIAS"
            ),
        }

    return output

# ============================================================
# REJECTED ALIAS SET
# ============================================================

def get_rejected_alias_set():

    rows = query_bq(
        f"""
        SELECT
            ALIAS

        FROM `{TABLE_ALIAS_REJECTED}`
        """
    )

    return {
        normalize(
            row["ALIAS"]
        )
        for row in rows
        if row.get("ALIAS")
    }
# ============================================================
# IS REJECTED
# ============================================================

def is_alias_rejected(
    raw_value: str,
    rejected_set: Optional[set] = None,
):

    if not raw_value:
        return False

    normalized = normalize(
        raw_value
    )

    if rejected_set is None:

        rejected_set = (
            get_rejected_alias_set()
        )

    return normalized in rejected_set

# ============================================================
# RESOLVE COMPANY
# ============================================================

def resolve_company_alias(
    raw_value: str,
    alias_map: Optional[Dict] = None,
):

    if not raw_value:
        return None

    if alias_map is None:

        alias_map = (
            get_company_alias_map()
        )

    normalized = normalize(
        raw_value
    )

    return alias_map.get(
        normalized
    )

# ============================================================
# RESOLVE SOLUTION
# ============================================================

def resolve_solution_alias(
    raw_value: str,
    alias_map: Optional[Dict] = None,
):

    if not raw_value:
        return None

    if alias_map is None:

        alias_map = (
            get_solution_alias_map()
        )

    normalized = normalize(
        raw_value
    )

    return alias_map.get(
        normalized
    )

# ============================================================
# INSERT REJECTED ALIAS
# ============================================================

def insert_rejected_alias(
    alias: str,
    entity_type: str,
):

    if not alias:
        return

    normalized = normalize(
        alias
    )

    existing = query_bq(
        f"""
        SELECT 1

        FROM `{TABLE_ALIAS_REJECTED}`

        WHERE UPPER(
            REGEXP_REPLACE(
                REPLACE(ALIAS, '+', ' PLUS '),
                r'[^A-Z0-9 ]',
                ' '
            )
        ) = @normalized

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
            ALIAS,
            ENTITY_TYPE,
            FIRST_SEEN_AT,
            LAST_SEEN_AT,
            NB_OCCURRENCES
        )

        VALUES (
            GENERATE_UUID(),
            @alias,
            @entity_type,
            CURRENT_TIMESTAMP(),
            CURRENT_TIMESTAMP(),
            '1'
        )
        """,
        {
            "alias": alias,
            "entity_type": entity_type,
        }
    )

# ============================================================
# RESOLVE ENTITIES
# ============================================================

def resolve_entities(
    raw_values: List[str],
):

    company_map = (
        get_company_alias_map()
    )

    solution_map = (
        get_solution_alias_map()
    )

    rejected_set = (
        get_rejected_alias_set()
    )

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

        # ====================================================
        # REJECTED
        # ====================================================

        if normalized in rejected_set:
            continue

        # ====================================================
        # COMPANY
        # ====================================================

        company = resolve_company_alias(
            raw,
            company_map,
        )

        if company:

            id_company = company[
                "id_company"
            ]

            if (
                id_company
                not in seen_companies
            ):

                companies.append({
                    "raw": raw,
                    "normalized": normalized,
                    "id_company": id_company,
                })

                seen_companies.add(
                    id_company
                )

            continue

        # ====================================================
        # SOLUTION
        # ====================================================

        solution = resolve_solution_alias(
            raw,
            solution_map,
        )

        if solution:

            id_solution = solution[
                "id_solution"
            ]

            if (
                id_solution
                not in seen_solutions
            ):

                solutions.append({
                    "raw": raw,
                    "normalized": normalized,
                    "id_solution": id_solution,
                })

                seen_solutions.add(
                    id_solution
                )

            continue

        # ====================================================
        # UNMATCHED
        # ====================================================

        if (
            normalized
            not in seen_unmatched
        ):

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
