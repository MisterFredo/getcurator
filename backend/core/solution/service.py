# ============================================================
# IMPORTS
# ============================================================

import uuid

from datetime import datetime

from typing import (
    Optional,
    List,
    Dict,
)

from google.cloud import bigquery

from config import (
    BQ_PROJECT,
    BQ_DATASET,
)

from utils.bigquery_utils import (
    query_bq,
    update_bq,
    get_bigquery_client,
)

from api.solution.models import (
    SolutionCreate,
    SolutionUpdate,
)

from core.matching.resolver import (
    normalize,
)

# ============================================================
# TABLES
# ============================================================

TABLE_SOLUTION = (
    f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_SOLUTION"
)

TABLE_COMPANY = (
    f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_COMPANY"
)

TABLE_NUMBERS_SOLUTION = (
    f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_NUMBERS_SOLUTION"
)

TABLE_COMPANY_UNIVERSE = (
    f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_COMPANY_UNIVERSE"
)

TABLE_SOLUTION_ALIAS = (
    f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_SOLUTION_ALIAS"
)

# ============================================================
# CREATE
# ============================================================

def create_solution(
    data: SolutionCreate,
) -> str:

    solution_id = str(
        uuid.uuid4()
    )

    now = (
        datetime.utcnow()
        .isoformat()
    )

    row = [{

        "ID_SOLUTION": solution_id,

        "NAME": data.name,

        "ID_COMPANY": data.id_company,

        "DESCRIPTION": (
            data.description
            or None
        ),

        "CONTENT": (
            data.content
            or None
        ),

        "CREATED_AT": now,

        "UPDATED_AT": now,

        "IS_ACTIVE": True,

    }]

    client = (
        get_bigquery_client()
    )

    client.load_table_from_json(

        row,

        TABLE_SOLUTION,

        job_config=(
            bigquery.LoadJobConfig(
                write_disposition="WRITE_APPEND",
            )
        ),

    ).result()

    # ========================================================
    # PRIMARY ALIAS
    # ========================================================

    create_solution_alias(

        id_solution=solution_id,

        alias=data.name,

    )

    # ========================================================
    # EXTRA ALIASES
    # ========================================================

    for alias in (
        data.aliases
        or []
    ):

        alias = alias.strip()

        if not alias:
            continue

        create_solution_alias(

            id_solution=solution_id,

            alias=alias,

        )

    return solution_id

# ============================================================
# LIST
# ============================================================

def list_solutions() -> List[Dict]:

    rows = query_bq(
        f"""
        SELECT
            s.ID_SOLUTION,
            s.NAME,
            s.ID_COMPANY,

            s.MEDIA_LOGO_RECTANGLE_ID
                AS SOLUTION_LOGO,

            c.NAME
                AS COMPANY_NAME,

            c.MEDIA_LOGO_RECTANGLE_ID,

            CAST(
                c.IS_PARTNER AS BOOL
            ) AS IS_PARTNER,

            s.CREATED_AT,
            s.UPDATED_AT,

            ns.ID_SOLUTION IS NOT NULL
                AS HAS_NUMBERS,

            ARRAY_AGG(
                DISTINCT u.LABEL
                IGNORE NULLS
            ) AS UNIVERSES

        FROM `{TABLE_SOLUTION}` s

        LEFT JOIN `{TABLE_COMPANY}` c
            ON c.ID_COMPANY = s.ID_COMPANY

        LEFT JOIN `{TABLE_COMPANY_UNIVERSE}` cu
            ON cu.ID_COMPANY = c.ID_COMPANY

        LEFT JOIN `{BQ_PROJECT}.{BQ_DATASET}.RATECARD_UNIVERSE` u
            ON u.ID_UNIVERSE = cu.ID_UNIVERSE

        LEFT JOIN (
            SELECT DISTINCT ID_SOLUTION
            FROM `{TABLE_NUMBERS_SOLUTION}`
        ) ns
            ON ns.ID_SOLUTION = s.ID_SOLUTION

        WHERE s.IS_ACTIVE = TRUE

        GROUP BY
            s.ID_SOLUTION,
            s.NAME,
            s.ID_COMPANY,
            s.MEDIA_LOGO_RECTANGLE_ID,
            c.NAME,
            c.MEDIA_LOGO_RECTANGLE_ID,
            c.IS_PARTNER,
            s.CREATED_AT,
            s.UPDATED_AT,
            ns.ID_SOLUTION

        ORDER BY UPPER(s.NAME)
        """
    )

    return [

        {
            "id_solution": r["ID_SOLUTION"],

            "name": r["NAME"],

            "id_company": r["ID_COMPANY"],

            "company_name": r.get(
                "COMPANY_NAME"
            ),

            "media_logo_rectangle_id": (
                r.get("SOLUTION_LOGO")
                or r.get(
                    "MEDIA_LOGO_RECTANGLE_ID"
                )
            ),

            "logo_type": (
                "solution"
                if r.get("SOLUTION_LOGO")
                else "company"
            ),

            "is_partner": r.get(
                "IS_PARTNER",
                False,
            ),

            "created_at": r.get(
                "CREATED_AT",
            ),

            "updated_at": r.get(
                "UPDATED_AT",
            ),

            "has_numbers": r.get(
                "HAS_NUMBERS",
                False,
            ),

            "universes": (
                r.get("UNIVERSES")
                or []
            ),

        }

        for r in rows

    ]


def list_solutions_for_user(
    user_id: str,
) -> List[Dict]:

    rows = query_bq(
        f"""
        SELECT
            s.ID_SOLUTION,
            s.NAME,
            s.ID_COMPANY,

            s.MEDIA_LOGO_RECTANGLE_ID
                AS SOLUTION_LOGO,

            c.NAME
                AS COMPANY_NAME,

            c.MEDIA_LOGO_RECTANGLE_ID,

            CAST(
                c.IS_PARTNER AS BOOL
            ) AS IS_PARTNER,

            s.CREATED_AT,
            s.UPDATED_AT,

            ns.ID_SOLUTION IS NOT NULL
                AS HAS_NUMBERS,

            ARRAY_AGG(
                DISTINCT u.LABEL
                IGNORE NULLS
            ) AS UNIVERSES

        FROM `{TABLE_SOLUTION}` s

        JOIN `{TABLE_COMPANY}` c
            ON c.ID_COMPANY = s.ID_COMPANY

        JOIN `{TABLE_COMPANY_UNIVERSE}` cu
            ON cu.ID_COMPANY = c.ID_COMPANY

        JOIN `{BQ_PROJECT}.{BQ_DATASET}.RATECARD_UNIVERSE` u
            ON u.ID_UNIVERSE = cu.ID_UNIVERSE

        JOIN `{BQ_PROJECT}.{BQ_DATASET}.RATECARD_USER_UNIVERSE` uu
            ON uu.ID_UNIVERSE = cu.ID_UNIVERSE

        LEFT JOIN (
            SELECT DISTINCT ID_SOLUTION
            FROM `{TABLE_NUMBERS_SOLUTION}`
        ) ns
            ON ns.ID_SOLUTION = s.ID_SOLUTION

        WHERE
            s.IS_ACTIVE = TRUE
            AND uu.ID_USER = @user_id

        GROUP BY
            s.ID_SOLUTION,
            s.NAME,
            s.ID_COMPANY,
            s.MEDIA_LOGO_RECTANGLE_ID,
            c.NAME,
            c.MEDIA_LOGO_RECTANGLE_ID,
            c.IS_PARTNER,
            s.CREATED_AT,
            s.UPDATED_AT,
            ns.ID_SOLUTION

        ORDER BY
            UPPER(s.NAME)
        """,
        {
            "user_id": user_id,
        },
    )

    return [
        {
            "id_solution": r["ID_SOLUTION"],

            "name": r["NAME"],

            "id_company": r["ID_COMPANY"],

            "company_name": r.get(
                "COMPANY_NAME"
            ),

            "media_logo_rectangle_id": (
                r.get("SOLUTION_LOGO")
                or r.get(
                    "MEDIA_LOGO_RECTANGLE_ID"
                )
            ),

            "logo_type": (
                "solution"
                if r.get("SOLUTION_LOGO")
                else "company"
            ),

            "is_partner": r.get(
                "IS_PARTNER",
                False,
            ),

            "created_at": r.get(
                "CREATED_AT",
            ),

            "updated_at": r.get(
                "UPDATED_AT",
            ),

            "has_numbers": r.get(
                "HAS_NUMBERS",
                False,
            ),

            "universes": (
                r.get("UNIVERSES")
                or []
            ),
        }
        for r in rows
    ]

# ============================================================
# GET ONE
# ============================================================

def get_solution(
    id_solution: str,
) -> Optional[Dict]:

    rows = query_bq(
        f"""
        SELECT
            s.*,

            c.NAME AS COMPANY_NAME,

            c.MEDIA_LOGO_RECTANGLE_ID
                AS COMPANY_LOGO,

            ns.ID_SOLUTION IS NOT NULL
                AS HAS_NUMBERS

        FROM `{TABLE_SOLUTION}` s

        LEFT JOIN `{TABLE_COMPANY}` c
            ON c.ID_COMPANY = s.ID_COMPANY

        LEFT JOIN (
            SELECT DISTINCT ID_SOLUTION
            FROM `{TABLE_NUMBERS_SOLUTION}`
        ) ns
            ON ns.ID_SOLUTION = s.ID_SOLUTION

        WHERE s.ID_SOLUTION = @id

        LIMIT 1
        """,
        {
            "id": id_solution,
        },
    )

    if not rows:
        return None

    r = rows[0]

    solution_logo = r.get(
        "MEDIA_LOGO_RECTANGLE_ID"
    )

    company_logo = r.get(
        "COMPANY_LOGO"
    )

    return {

        "id_solution": r["ID_SOLUTION"],

        "name": r["NAME"],

        "id_company": r["ID_COMPANY"],

        "company_name": r.get(
            "COMPANY_NAME"
        ),

        "description": r.get(
            "DESCRIPTION"
        ),

        "content": r.get(
            "CONTENT"
        ),

        "media_logo_rectangle_id": (
            solution_logo
            or company_logo
        ),

        "logo_type": (
            "solution"
            if solution_logo
            else "company"
        ),

        "aliases": get_solution_aliases(
            id_solution
        ),

        "created_at": r.get(
            "CREATED_AT"
        ),

        "updated_at": r.get(
            "UPDATED_AT"
        ),

        "has_numbers": r.get(
            "HAS_NUMBERS",
            False,
        ),

    }
# ============================================================
# UPDATE
# ============================================================

def update_solution(
    id_solution: str,
    data: SolutionUpdate,
) -> bool:

    values = data.dict(
        exclude_unset=True
    )

    if not values:
        return False

    mapping = {
        "name": "NAME",
        "id_company": "ID_COMPANY",
        "description": "DESCRIPTION",
        "content": "CONTENT",
    }

    bq_values = {
        mapping[k]: v
        for k, v in values.items()
        if k in mapping
    }

    if bq_values:

        bq_values["UPDATED_AT"] = (
            datetime.utcnow()
            .isoformat()
        )

        update_bq(
            table=TABLE_SOLUTION,
            fields=bq_values,
            where={
                "ID_SOLUTION": id_solution,
            },
        )

    return True


# ============================================================
# DELETE (SOFT)
# ============================================================

def delete_solution(
    id_solution: str,
) -> bool:

    existing = query_bq(
        f"""
        SELECT ID_SOLUTION

        FROM `{TABLE_SOLUTION}`

        WHERE ID_SOLUTION = @id
        """,
        {
            "id": id_solution,
        },
    )

    if not existing:
        return False

    return update_bq(
        table=TABLE_SOLUTION,
        fields={
            "IS_ACTIVE": False,
            "UPDATED_AT": (
                datetime.utcnow()
                .isoformat()
            ),
        },
        where={
            "ID_SOLUTION": id_solution,
        },
    )
# ============================================================
# SOLUTION ALIASES
# ============================================================

# ============================================================
# SOLUTION ALIASES
# ============================================================

def get_solution_aliases(
    id_solution: str,
) -> List[Dict]:

    rows = query_bq(
        f"""
        SELECT
            ALIAS

        FROM `{TABLE_SOLUTION_ALIAS}`

        WHERE ID_SOLUTION = @id_solution

        ORDER BY UPPER(ALIAS)
        """,
        {
            "id_solution": id_solution,
        },
    )

    return [
        {
            "alias": r["ALIAS"],
        }
        for r in rows
    ]


# ============================================================

def create_solution_alias(
    id_solution: str,
    alias: str,
) -> bool:

    alias = (
        alias
        or ""
    ).strip()

    if not alias:

        raise ValueError(
            "Alias vide."
        )

    normalized_alias = normalize(
        alias
    )

    existing = query_bq(
        f"""
        SELECT 1

        FROM `{TABLE_SOLUTION_ALIAS}`

        WHERE UPPER(
            REGEXP_REPLACE(
                REPLACE(ALIAS, '+', ' PLUS '),
                r'[^A-Z0-9 ]',
                ' '
            )
        ) = @normalized_alias

        LIMIT 1
        """,
        {
            "normalized_alias": normalized_alias,
        },
    )

    if existing:
        return False

    query_bq(
        f"""
        INSERT INTO `{TABLE_SOLUTION_ALIAS}` (
            ALIAS,
            ID_SOLUTION
        )

        VALUES (
            @alias,
            @id_solution
        )
        """,
        {
            "alias": alias,
            "id_solution": id_solution,
        },
    )

    return True


# ============================================================

def delete_solution_alias(
    id_solution: str,
    alias: str,
) -> bool:

    alias = (
        alias
        or ""
    ).strip()

    if not alias:
        return False

    solution = get_solution(
        id_solution
    )

    if not solution:

        raise ValueError(
            "Solution introuvable."
        )

    if normalize(alias) == normalize(
        solution["name"] or ""
    ):

        raise ValueError(
            "Impossible de supprimer l'alias principal."
        )

    normalized_alias = normalize(
        alias
    )

    query_bq(
        f"""
        DELETE FROM `{TABLE_SOLUTION_ALIAS}`

        WHERE ID_SOLUTION = @id_solution

        AND UPPER(
            REGEXP_REPLACE(
                REPLACE(ALIAS, '+', ' PLUS '),
                r'[^A-Z0-9 ]',
                ' '
            )
        ) = @normalized_alias
        """,
        {
            "id_solution": id_solution,
            "normalized_alias": normalized_alias,
        },
    )

    return True
