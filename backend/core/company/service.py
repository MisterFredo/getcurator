# backend/core/company/service.py

import uuid
from datetime import datetime
from typing import Optional, Dict, List

from google.cloud import bigquery

from config import BQ_PROJECT, BQ_DATASET
from utils.bigquery_utils import (
    query_bq,
    update_bq,
    get_bigquery_client,
)
from api.company.models import CompanyCreate, CompanyUpdate


TABLE_COMPANY = f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_COMPANY"
TABLE_NUMBERS_COMPANY = f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_NUMBERS_COMPANY"
TABLE_COMPANY_UNIVERSE = f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_COMPANY_UNIVERSE"
TABLE_COMPANY_ALIAS = f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_COMPANY_ALIAS"

VIEW_STATS_COMPANY = f"{BQ_PROJECT}.{BQ_DATASET}.V_CONTENT_STATS_COMPANY"

ALLOWED_FREQUENCIES = ["WEEKLY", "MONTHLY", "QUARTERLY"]


# ============================================================
# CREATE COMPANY
# ============================================================

def create_company(data: CompanyCreate) -> str:

    if not data.universes:
        raise ValueError("Company must have at least one universe")

    company_id = str(uuid.uuid4())
    now = datetime.utcnow().isoformat()

    insight_frequency = data.insight_frequency or "QUARTERLY"

    if insight_frequency not in ALLOWED_FREQUENCIES:
        raise ValueError("Invalid insight_frequency")

    row = [{
        "ID_COMPANY": company_id,
        "NAME": data.name,
        "TYPE": data.type,
        "DESCRIPTION": data.description or None,
        "MEDIA_LOGO_RECTANGLE_ID": None,
        "LINKEDIN_URL": data.linkedin_url or None,
        "WEBSITE_URL": data.website_url or None,
        "IS_PARTNER": bool(data.is_partner),
        "INSIGHT_FREQUENCY": insight_frequency,
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

    assign_company_universes(
        company_id,
        data.universes,
    )

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

def assign_company_universes(
    company_id: str,
    universes: List[str],
):

    query_bq(f"""
        DELETE FROM `{TABLE_COMPANY_UNIVERSE}`
        WHERE ID_COMPANY = @company_id
    """, {
        "company_id": company_id,
    })

    for u in universes:

        query_bq(f"""
            INSERT INTO `{TABLE_COMPANY_UNIVERSE}` (
                ID_COMPANY,
                ID_UNIVERSE,
                CREATED_AT
            )
            VALUES (
                @company_id,
                @universe,
                CURRENT_TIMESTAMP()
            )
        """, {
            "company_id": company_id,
            "universe": u,
        })


def get_company_universes(
    company_id: str
) -> List[str]:

    rows = query_bq(f"""
        SELECT ID_UNIVERSE
        FROM `{TABLE_COMPANY_UNIVERSE}`
        WHERE ID_COMPANY = @company_id
    """, {
        "company_id": company_id,
    })

    return [r["ID_UNIVERSE"] for r in rows]


# ============================================================
# LIST COMPANIES
# ============================================================

def list_companies(
    universe_id: Optional[str] = None
) -> List[Dict]:

    params = {}
    universe_filter = ""

    if universe_id:
        universe_filter = "AND cu.ID_UNIVERSE = @universe_id"
        params["universe_id"] = universe_id

    sql = f"""
    SELECT
        c.ID_COMPANY,
        c.NAME,
        c.TYPE,

        CAST(c.IS_PARTNER AS BOOL) AS IS_PARTNER,

        c.MEDIA_LOGO_RECTANGLE_ID,
        c.INSIGHT_FREQUENCY,

        COALESCE(m.total, 0) AS NB_ANALYSES,
        COALESCE(m.last_30_days, 0) AS DELTA_30D,

        CASE
            WHEN c.DESCRIPTION IS NOT NULL
             AND TRIM(c.DESCRIPTION) != ""
            THEN TRUE
            ELSE FALSE
        END AS HAS_DESCRIPTION,

        CASE
            WHEN c.WIKI_CONTENT IS NOT NULL
             AND TRIM(c.WIKI_CONTENT) != ""
            THEN TRUE
            ELSE FALSE
        END AS HAS_WIKI,

        nc.ID_COMPANY IS NOT NULL AS HAS_NUMBERS,

        r.ID_INSIGHT,
        r.KEY_POINTS,

        ARRAY_AGG(
            DISTINCT u.LABEL IGNORE NULLS
        ) AS universes

    FROM `{TABLE_COMPANY}` c

    LEFT JOIN `{TABLE_COMPANY_UNIVERSE}` cu
        ON cu.ID_COMPANY = c.ID_COMPANY

    LEFT JOIN `{BQ_PROJECT}.{BQ_DATASET}.RATECARD_UNIVERSE` u
        ON u.ID_UNIVERSE = cu.ID_UNIVERSE

    LEFT JOIN `{VIEW_STATS_COMPANY}` m
        ON m.id_company = c.ID_COMPANY

    LEFT JOIN (
        SELECT DISTINCT ID_COMPANY
        FROM `{TABLE_NUMBERS_COMPANY}`
    ) nc
        ON nc.ID_COMPANY = c.ID_COMPANY

    LEFT JOIN (
        SELECT *
        FROM `{BQ_PROJECT}.{BQ_DATASET}.RATECARD_RADAR`
        WHERE STATUS = "GENERATED"

        QUALIFY ROW_NUMBER() OVER (
            PARTITION BY ENTITY_ID
            ORDER BY YEAR DESC, PERIOD DESC
        ) = 1
    ) r
        ON r.ENTITY_ID = c.ID_COMPANY
       AND r.ENTITY_TYPE = "company"

    WHERE c.IS_ACTIVE = TRUE
    {universe_filter}

    GROUP BY
        c.ID_COMPANY,
        c.NAME,
        c.TYPE,
        c.IS_PARTNER,
        c.MEDIA_LOGO_RECTANGLE_ID,
        c.INSIGHT_FREQUENCY,
        m.total,
        m.last_30_days,
        HAS_DESCRIPTION,
        HAS_WIKI,
        HAS_NUMBERS,
        r.ID_INSIGHT,
        r.KEY_POINTS

    ORDER BY UPPER(c.NAME)
    """

    rows = query_bq(sql, params)

    return [
        {
            "id_company": r["ID_COMPANY"],
            "name": r["NAME"],
            "type": r.get("TYPE"),
            "is_partner": r["IS_PARTNER"],
            "media_logo_rectangle_id": r["MEDIA_LOGO_RECTANGLE_ID"],
            "insight_frequency": r.get("INSIGHT_FREQUENCY"),
            "nb_analyses": r["NB_ANALYSES"],
            "delta_30d": r["DELTA_30D"],
            "has_description": r["HAS_DESCRIPTION"],
            "has_wiki": r["HAS_WIKI"],
            "has_numbers": r.get("HAS_NUMBERS", False),

            "last_radar": {
                "id_insight": r["ID_INSIGHT"],
                "key_points": r["KEY_POINTS"],
            } if r.get("ID_INSIGHT") else None,

            "universes": r.get("universes") or [],
        }
        for r in rows
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


def list_companies_for_user(
    user_id: str
):

    sql = f"""
    SELECT
        c.ID_COMPANY,
        c.NAME,
        c.TYPE,

        CAST(c.IS_PARTNER AS BOOL) AS IS_PARTNER,

        c.MEDIA_LOGO_RECTANGLE_ID,
        c.INSIGHT_FREQUENCY,

        COALESCE(m.total, 0) AS NB_ANALYSES,
        COALESCE(m.last_30_days, 0) AS DELTA_30D,

        ARRAY_AGG(
            DISTINCT u.LABEL IGNORE NULLS
        ) AS universes

    FROM `{TABLE_COMPANY}` c

    JOIN `{TABLE_COMPANY_UNIVERSE}` cu
        ON cu.ID_COMPANY = c.ID_COMPANY

    JOIN `{BQ_PROJECT}.{BQ_DATASET}.RATECARD_UNIVERSE` u
        ON u.ID_UNIVERSE = cu.ID_UNIVERSE

    JOIN `{BQ_PROJECT}.{BQ_DATASET}.RATECARD_USER_UNIVERSE` uu
        ON uu.ID_UNIVERSE = cu.ID_UNIVERSE

    LEFT JOIN `{VIEW_STATS_COMPANY}` m
        ON m.id_company = c.ID_COMPANY

    WHERE
        c.IS_ACTIVE = TRUE
        AND uu.ID_USER = @user_id

    GROUP BY
        c.ID_COMPANY,
        c.NAME,
        c.TYPE,
        c.IS_PARTNER,
        c.MEDIA_LOGO_RECTANGLE_ID,
        c.INSIGHT_FREQUENCY,
        m.total,
        m.last_30_days

    HAVING COALESCE(m.total, 0) >= 1

    ORDER BY UPPER(c.NAME)
    """

    rows = query_bq(sql, {
        "user_id": user_id,
    })

    return [
        {
            "id_company": r["ID_COMPANY"],
            "name": r["NAME"],
            "type": r.get("TYPE"),
            "is_partner": r["IS_PARTNER"],
            "media_logo_rectangle_id": r["MEDIA_LOGO_RECTANGLE_ID"],
            "insight_frequency": r.get("INSIGHT_FREQUENCY"),
            "nb_analyses": r["NB_ANALYSES"],
            "delta_30d": r["DELTA_30D"],
            "aliases": get_company_aliases(company_id),
            "universes": r.get("universes") or [],
        }
        for r in rows
    ]


# ============================================================
# GET ONE COMPANY
# ============================================================

def get_company(
    company_id: str
) -> Optional[Dict]:

    rows = query_bq(f"""
        SELECT
            c.*,
            nc.ID_COMPANY IS NOT NULL AS HAS_NUMBERS

        FROM `{TABLE_COMPANY}` c

        LEFT JOIN (
            SELECT DISTINCT ID_COMPANY
            FROM `{TABLE_NUMBERS_COMPANY}`
        ) nc
            ON nc.ID_COMPANY = c.ID_COMPANY

        WHERE c.ID_COMPANY = @id

        LIMIT 1
    """, {
        "id": company_id,
    })

    if not rows:
        return None

    r = rows[0]

    return {
        "id_company": r["ID_COMPANY"],
        "name": r["NAME"],
        "type": r.get("TYPE"),
        "description": r.get("DESCRIPTION"),

        "wiki_content": r.get("WIKI_CONTENT"),
        "wiki_source_id": r.get("WIKI_SOURCE_ID"),
        "wiki_updated_at": r.get("WIKI_UPDATED_AT"),
        "wiki_vectorised": r.get("WIKI_VECTORISED", False),

        "media_logo_rectangle_id": r.get("MEDIA_LOGO_RECTANGLE_ID"),
        "linkedin_url": r.get("LINKEDIN_URL"),
        "website_url": r.get("WEBSITE_URL"),

        "is_partner": r.get("IS_PARTNER", False),
        "is_active": r.get("IS_ACTIVE", True),

        "insight_frequency": r.get("INSIGHT_FREQUENCY"),

        "has_numbers": r.get("HAS_NUMBERS", False),
        "universes": get_company_universes(company_id),

        "created_at": r.get("CREATED_AT"),
        "updated_at": r.get("UPDATED_AT"),
    }


# ============================================================
# UPDATE
# ============================================================

def update_company(
    id_company: str,
    data: CompanyUpdate
) -> bool:

    values = data.dict(exclude_unset=True)
    universes = values.pop("universes", None)

    if not values and universes is None:
        return False

    mapping = {
        "name": "NAME",
        "type": "TYPE",
        "description": "DESCRIPTION",
        "linkedin_url": "LINKEDIN_URL",
        "website_url": "WEBSITE_URL",
        "is_partner": "IS_PARTNER",
        "wiki_content": "WIKI_CONTENT",
        "insight_frequency": "INSIGHT_FREQUENCY",
    }

    bq_values = {
        mapping[k]: v
        for k, v in values.items()
        if k in mapping
    }

    if "INSIGHT_FREQUENCY" in bq_values:
        if bq_values["INSIGHT_FREQUENCY"] not in ALLOWED_FREQUENCIES:
            raise ValueError("Invalid insight_frequency")

    if "WIKI_CONTENT" in bq_values:
        bq_values["WIKI_UPDATED_AT"] = datetime.utcnow().isoformat()
        bq_values["WIKI_VECTORISED"] = False

    if bq_values:

        bq_values["UPDATED_AT"] = datetime.utcnow().isoformat()

        update_bq(
            table=TABLE_COMPANY,
            fields=bq_values,
            where={"ID_COMPANY": id_company},
        )

    if universes is not None:
        assign_company_universes(id_company, universes)

    return True


# ============================================================
# DELETE (SOFT)
# ============================================================

def delete_company(
    id_company: str
) -> bool:

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

def get_company_aliases(
    id_company: str
) -> List[Dict]:

    rows = query_bq(f"""
        SELECT
            ALIAS,
            MATCH_STATUS

        FROM `{TABLE_COMPANY_ALIAS}`

        WHERE ID_COMPANY = @id_company

        ORDER BY UPPER(ALIAS)
    """, {
        "id_company": id_company,
    })

    return [
        {
            "alias": r["ALIAS"],
            "match_status": r["MATCH_STATUS"],
        }
        for r in rows
    ]


def create_company_alias(
    id_company: str,
    alias: str,
):

    alias = (alias or "").strip()

    if not alias:
        raise ValueError("alias vide")

    query_bq(f"""
        MERGE `{TABLE_COMPANY_ALIAS}` t

        USING (
            SELECT
                @alias AS ALIAS,
                @id_company AS ID_COMPANY
        ) s

        ON UPPER(TRIM(t.ALIAS))
           =
           UPPER(TRIM(s.ALIAS))

        WHEN NOT MATCHED THEN

        INSERT (
            ALIAS,
            ID_COMPANY,
            MATCH_STATUS
        )

        VALUES (
            s.ALIAS,
            s.ID_COMPANY,
            'MATCH'
        )
    """, {
        "alias": alias,
        "id_company": id_company,
    })

    return True


# ============================================================
# ADD COMPANY ALIAS
# ============================================================

def add_company_alias(
    id_company: str,
    alias: str,
):

    alias = (alias or "").strip()

    if not alias:
        raise ValueError("alias vide")

    rows = query_bq(f"""
        SELECT 1

        FROM `{TABLE_COMPANY_ALIAS}`

        WHERE
            ID_COMPANY = @id_company
            AND UPPER(TRIM(ALIAS))
                =
                UPPER(TRIM(@alias))

        LIMIT 1
    """, {
        "id_company": id_company,
        "alias": alias,
    })

    if rows:
        return False

    query_bq(f"""
        INSERT INTO `{TABLE_COMPANY_ALIAS}` (
            ALIAS,
            ID_COMPANY,
            MATCH_STATUS
        )

        VALUES (
            @alias,
            @id_company,
            'MATCH'
        )
    """, {
        "alias": alias,
        "id_company": id_company,
    })

    return True


def delete_company_alias(
    id_company: str,
    alias: str,
):

    alias = (alias or "").strip()

    if not alias:
        return False

    # ========================================================
    # PROTECT MAIN NAME
    # ========================================================

    company = get_company(id_company)

    if not company:
        raise ValueError("company introuvable")

    if alias.upper().strip() == (
        company["name"] or ""
    ).upper().strip():

        raise ValueError(
            "Impossible de supprimer l'alias principal"
        )

    query_bq(f"""
        DELETE FROM `{TABLE_COMPANY_ALIAS}`

        WHERE ID_COMPANY = @id_company

        AND UPPER(TRIM(ALIAS))
            =
            UPPER(TRIM(@alias))
    """, {
        "id_company": id_company,
        "alias": alias,
    })

    return True
