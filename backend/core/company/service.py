# backend/core/company/service.py

import uuid
from datetime import datetime
from typing import Dict, List, Optional

from google.cloud import bigquery

from config import BQ_DATASET, BQ_PROJECT

from api.company.models import (
    CompanyCreate,
    CompanyUpdate,
)

from core.matching.resolver import normalize

from utils.bigquery_utils import (
    get_bigquery_client,
    query_bq,
    update_bq,
)

# ============================================================
# TABLES
# ============================================================

TABLE_COMPANY = (
    f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_COMPANY"
)

TABLE_COMPANY_ALIAS = (
    f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_COMPANY_ALIAS"
)

TABLE_COMPANY_UNIVERSE = (
    f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_COMPANY_UNIVERSE"
)
# ============================================================
# CREATE COMPANY
# ============================================================

# ============================================================
# CREATE
# ============================================================

def create_company(
    data: CompanyCreate,
) -> str:

    if not data.universes:

        raise ValueError(
            "Company must have at least one universe"
        )

    company_id = str(uuid.uuid4())

    now = datetime.utcnow().isoformat()

    row = [{
        "ID_COMPANY": company_id,
        "NAME": data.name,
        "TYPE": data.type,
        "DESCRIPTION": (
            data.description
            or None
        ),
        "MEDIA_LOGO_RECTANGLE_ID": None,
        "LINKEDIN_URL": (
            data.linkedin_url
            or None
        ),
        "WEBSITE_URL": (
            data.website_url
            or None
        ),
        "IS_PARTNER": bool(
            data.is_partner
        ),
        "CREATED_AT": now,
        "UPDATED_AT": now,
        "IS_ACTIVE": True,
    }]

    client = get_bigquery_client()

    client.load_table_from_json(
        row,
        TABLE_COMPANY,
        job_config=bigquery.LoadJobConfig(
            write_disposition="WRITE_APPEND"
        ),
    ).result()

    # ========================================================
    # UNIVERSES
    # ========================================================

    assign_company_universes(
        company_id,
        data.universes,
    )

    # ========================================================
    # ALIASES
    # ========================================================

    create_company_alias(
        id_company=company_id,
        alias=data.name,
    )

    for alias in data.aliases or []:

        alias = alias.strip()

        if not alias:
            continue

        create_company_alias(
            id_company=company_id,
            alias=alias,
        )

    return company_id

# ============================================================
# UNIVERS
# ============================================================

# ============================================================
# UNIVERSES
# ============================================================

def assign_company_universes(
    company_id: str,
    universe_ids: List[str],
) -> None:
    """
    Remplace les univers associés à une société.
    """

    query_bq(
        f"""
        DELETE FROM `{TABLE_COMPANY_UNIVERSE}`
        WHERE ID_COMPANY = @company_id
        """,
        {
            "company_id": company_id,
        },
    )

    for universe_id in universe_ids:

        query_bq(
            f"""
            INSERT INTO `{TABLE_COMPANY_UNIVERSE}` (
                ID_COMPANY,
                ID_UNIVERSE,
                CREATED_AT
            )
            VALUES (
                @company_id,
                @universe_id,
                CURRENT_TIMESTAMP()
            )
            """,
            {
                "company_id": company_id,
                "universe_id": universe_id,
            },
        )


def get_company_universes(
    company_id: str,
) -> List[str]:
    """
    Retourne les identifiants des univers associés
    à une société.
    """

    rows = query_bq(
        f"""
        SELECT
            ID_UNIVERSE
        FROM `{TABLE_COMPANY_UNIVERSE}`
        WHERE ID_COMPANY = @company_id
        """,
        {
            "company_id": company_id,
        },
    )

    return [
        row["ID_UNIVERSE"]
        for row in rows
    ]
# ============================================================
# LIST COMPANIES
# ============================================================

# ============================================================
# LIST
# ============================================================

def list_companies(
    universe_id: Optional[str] = None,
) -> List[Dict]:

    params = {}

    universe_filter = ""

    if universe_id:

        universe_filter = """
        AND cu.ID_UNIVERSE = @universe_id
        """

        params["universe_id"] = universe_id

    sql = f"""
    SELECT
        c.ID_COMPANY,
        c.NAME,
        c.TYPE,

        CAST(
            c.IS_PARTNER AS BOOL
        ) AS IS_PARTNER,

        c.DESCRIPTION,

        c.MEDIA_LOGO_RECTANGLE_ID,

        c.LINKEDIN_URL,

        c.WEBSITE_URL,

        ARRAY_AGG(
            DISTINCT u.LABEL
            IGNORE NULLS
        ) AS UNIVERSES

    FROM `{TABLE_COMPANY}` c

    LEFT JOIN `{TABLE_COMPANY_UNIVERSE}` cu
        ON cu.ID_COMPANY = c.ID_COMPANY

    LEFT JOIN `{BQ_PROJECT}.{BQ_DATASET}.RATECARD_UNIVERSE` u
        ON u.ID_UNIVERSE = cu.ID_UNIVERSE

    WHERE c.IS_ACTIVE = TRUE

    {universe_filter}

    GROUP BY
        c.ID_COMPANY,
        c.NAME,
        c.TYPE,
        c.IS_PARTNER,
        c.DESCRIPTION,
        c.MEDIA_LOGO_RECTANGLE_ID,
        c.LINKEDIN_URL,
        c.WEBSITE_URL

    ORDER BY
        UPPER(c.NAME)
    """

    rows = query_bq(
        sql,
        params,
    )

    return [
        {
            "id_company":
                row["ID_COMPANY"],

            "name":
                row["NAME"],

            "type":
                row.get("TYPE"),

            "description":
                row.get("DESCRIPTION"),

            "is_partner":
                row["IS_PARTNER"],

            "media_logo_rectangle_id":
                row.get(
                    "MEDIA_LOGO_RECTANGLE_ID"
                ),

            "linkedin_url":
                row.get(
                    "LINKEDIN_URL"
                ),

            "website_url":
                row.get(
                    "WEBSITE_URL"
                ),

            "universes":
                row.get(
                    "UNIVERSES"
                ) or [],
        }

        for row in rows
    ]

def list_company_types():

    rows = query_bq(f"""
        SELECT
            ID_TYPE,
            LABEL
        FROM `{BQ_PROJECT}.{BQ_DATASET}.RATECARD_COMPANY_TYPE`
        ORDER BY LABEL
    """)

    return [
        {
            "id_type": r["ID_TYPE"],
            "label": r["LABEL"],
        }
        for r in rows
    ]

# ============================================================
# LIST FOR USER
# ============================================================

def list_companies_for_user(
    user_id: str,
) -> List[Dict]:

    sql = f"""
    SELECT
        c.ID_COMPANY,
        c.NAME,
        c.TYPE,

        CAST(
            c.IS_PARTNER AS BOOL
        ) AS IS_PARTNER,

        c.MEDIA_LOGO_RECTANGLE_ID,

        ARRAY_AGG(
            DISTINCT u.LABEL
            IGNORE NULLS
        ) AS UNIVERSES

    FROM `{TABLE_COMPANY}` c

    JOIN `{TABLE_COMPANY_UNIVERSE}` cu
        ON cu.ID_COMPANY = c.ID_COMPANY

    JOIN `{BQ_PROJECT}.{BQ_DATASET}.RATECARD_UNIVERSE` u
        ON u.ID_UNIVERSE = cu.ID_UNIVERSE

    JOIN `{BQ_PROJECT}.{BQ_DATASET}.RATECARD_USER_UNIVERSE` uu
        ON uu.ID_UNIVERSE = cu.ID_UNIVERSE

    WHERE
        c.IS_ACTIVE = TRUE
        AND uu.ID_USER = @user_id

    GROUP BY
        c.ID_COMPANY,
        c.NAME,
        c.TYPE,
        c.IS_PARTNER,
        c.MEDIA_LOGO_RECTANGLE_ID

    ORDER BY
        UPPER(c.NAME)
    """

    rows = query_bq(
        sql,
        {
            "user_id": user_id,
        },
    )

    alias_rows = query_bq(
        f"""
        SELECT
            ID_COMPANY,
            ALIAS

        FROM `{TABLE_COMPANY_ALIAS}`
        """
    )

    aliases_map = {}

    for row in alias_rows:

        aliases_map.setdefault(
            row["ID_COMPANY"],
            [],
        ).append({
            "alias": row["ALIAS"],
        })

    return [
        {
            "id_company":
                row["ID_COMPANY"],

            "name":
                row["NAME"],

            "type":
                row.get("TYPE"),

            "is_partner":
                row["IS_PARTNER"],

            "media_logo_rectangle_id":
                row.get(
                    "MEDIA_LOGO_RECTANGLE_ID"
                ),

            "aliases":
                aliases_map.get(
                    row["ID_COMPANY"],
                    [],
                ),

            "universes":
                row.get(
                    "UNIVERSES"
                ) or [],
        }

        for row in rows
    ]
# ============================================================
# GET ONE COMPANY
# ============================================================

# ============================================================
# GET
# ============================================================

def get_company(
    company_id: str,
) -> Optional[Dict]:

    rows = query_bq(
        f"""
        SELECT *
        FROM `{TABLE_COMPANY}`
        WHERE ID_COMPANY = @company_id
        LIMIT 1
        """,
        {
            "company_id": company_id,
        },
    )

    if not rows:
        return None

    row = rows[0]

    return {
        "id_company":
            row["ID_COMPANY"],

        "name":
            row["NAME"],

        "type":
            row.get("TYPE"),

        "description":
            row.get("DESCRIPTION"),

        "wiki_content":
            row.get("WIKI_CONTENT"),

        "wiki_source_id":
            row.get("WIKI_SOURCE_ID"),

        "wiki_updated_at":
            row.get("WIKI_UPDATED_AT"),

        "wiki_vectorised":
            row.get(
                "WIKI_VECTORISED",
                False,
            ),

        "media_logo_rectangle_id":
            row.get(
                "MEDIA_LOGO_RECTANGLE_ID"
            ),

        "linkedin_url":
            row.get(
                "LINKEDIN_URL"
            ),

        "website_url":
            row.get(
                "WEBSITE_URL"
            ),

        "is_partner":
            row.get(
                "IS_PARTNER",
                False,
            ),

        "is_active":
            row.get(
                "IS_ACTIVE",
                True,
            ),

        "universes":
            get_company_universes(
                company_id
            ),

        "created_at":
            row.get(
                "CREATED_AT"
            ),

        "updated_at":
            row.get(
                "UPDATED_AT"
            ),
    }

# ============================================================
# UPDATE
# ============================================================

# ============================================================
# UPDATE
# ============================================================

def update_company(
    id_company: str,
    data: CompanyUpdate,
) -> bool:

    values = data.dict(
        exclude_unset=True
    )

    universes = values.pop(
        "universes",
        None,
    )

    if (
        not values
        and universes is None
    ):
        return False

    mapping = {
        "name": "NAME",
        "type": "TYPE",
        "description": "DESCRIPTION",
        "linkedin_url": "LINKEDIN_URL",
        "website_url": "WEBSITE_URL",
        "is_partner": "IS_PARTNER",
        "wiki_content": "WIKI_CONTENT",
    }

    bq_values = {
        mapping[key]: value
        for key, value in values.items()
        if key in mapping
    }

    # ========================================================
    # WIKI
    # ========================================================

    if "WIKI_CONTENT" in bq_values:

        bq_values[
            "WIKI_UPDATED_AT"
        ] = datetime.utcnow().isoformat()

        bq_values[
            "WIKI_VECTORISED"
        ] = False

    # ========================================================
    # UPDATE
    # ========================================================

    if bq_values:

        bq_values[
            "UPDATED_AT"
        ] = datetime.utcnow().isoformat()

        update_bq(
            table=TABLE_COMPANY,
            fields=bq_values,
            where={
                "ID_COMPANY": id_company,
            },
        )

    # ========================================================
    # UNIVERSES
    # ========================================================

    if universes is not None:

        assign_company_universes(
            id_company,
            universes,
        )

    return True


# ============================================================
# DELETE (SOFT)
# ============================================================

def delete_company(id_company: str) -> bool:

    return update_bq(
        table=TABLE_COMPANY,
        fields={
            "IS_ACTIVE": False,
            "UPDATED_AT": datetime.utcnow().isoformat(),
        },
        where={"ID_COMPANY": id_company},
    )

# ============================================================
# COMPANY ALIASES
# ============================================================

# ============================================================
# ALIASES
# ============================================================

def get_company_aliases(
    id_company: str,
) -> List[Dict]:

    rows = query_bq(
        f"""
        SELECT
            ALIAS

        FROM `{TABLE_COMPANY_ALIAS}`

        WHERE ID_COMPANY = @id_company

        ORDER BY
            UPPER(ALIAS)
        """,
        {
            "id_company": id_company,
        },
    )

    return [
        {
            "alias": row["ALIAS"],
        }
        for row in rows
    ]
# ============================================================
# CREATE COMPANY ALIAS
# ============================================================

# ============================================================
# CREATE ALIAS
# ============================================================

# ============================================================
# CREATE ALIAS
# ============================================================

def create_company_alias(
    id_company: str,
    alias: str,
) -> bool:

    alias = (alias or "").strip()

    if not alias:
        raise ValueError(
            "Alias vide."
        )

    normalized_alias = normalize(
        alias
    )

    existing = query_bq(
        f"""
        SELECT
            ALIAS,
            ID_COMPANY

        FROM `{TABLE_COMPANY_ALIAS}`

        WHERE
            UPPER(
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

        raise ValueError(
            f'L\'alias "{alias}" existe déjà.'
        )

    query_bq(
        f"""
        INSERT INTO `{TABLE_COMPANY_ALIAS}` (
            ID_COMPANY,
            ALIAS
        )

        VALUES (
            @id_company,
            @alias
        )
        """,
        {
            "id_company": id_company,
            "alias": alias,
        },
    )

    return True


# ============================================================
# DELETE COMPANY ALIAS
# ============================================================

# ============================================================
# DELETE ALIAS
# ============================================================

def delete_company_alias(
    id_company: str,
    alias: str,
) -> bool:

    alias = (alias or "").strip()

    if not alias:
        return False

    company = get_company(
        id_company
    )

    if not company:

        raise ValueError(
            "Company introuvable."
        )

    # ========================================================
    # MAIN ALIAS
    # ========================================================

    if normalize(alias) == normalize(
        company["name"] or ""
    ):

        raise ValueError(
            "Impossible de supprimer l'alias principal."
        )

    normalized_alias = normalize(
        alias
    )

    query_bq(
        f"""
        DELETE FROM `{TABLE_COMPANY_ALIAS}`

        WHERE
            ID_COMPANY = @id_company

        AND
            UPPER(
                REGEXP_REPLACE(
                    REPLACE(ALIAS, '+', ' PLUS '),
                    r'[^A-Z0-9 ]',
                    ' '
                )
            ) = @normalized_alias
        """,
        {
            "id_company": id_company,
            "normalized_alias": normalized_alias,
        },
    )

    return True
