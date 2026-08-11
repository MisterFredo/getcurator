# backend/core/company/public_service.py

from typing import List, Dict, Optional

from config import (
    BQ_PROJECT,
    BQ_DATASET,
)

from utils.bigquery_utils import (
    query_bq,
)

from core.company.service import (
    get_company,
)


# ============================================================
# TABLES / VIEWS
# ============================================================

TABLE_COMPANY_UNIVERSE = (
    f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_COMPANY_UNIVERSE"
)

TABLE_COMPANY = (
    f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_COMPANY"
)

TABLE_COMPANY_ALIAS = (
    f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_COMPANY_ALIAS"
)

TABLE_CONTENT_ENRICHED = (
    f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_CONTENT_ENRICHED"
)


# ============================================================
# PUBLIC VIEW
# ============================================================

def get_company_view(
    company_id: str,
) -> Optional[Dict]:

    company = get_company(
        company_id,
    )

    if not company:

        return None

    return company


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

        COALESCE(
            cc.CONTENT_COUNT,
            0
        ) AS CONTENT_COUNT,

        ARRAY_AGG(
            DISTINCT u.LABEL
            IGNORE NULLS
        ) AS UNIVERSES

    FROM `{TABLE_COMPANY}` c

    JOIN `{TABLE_COMPANY_UNIVERSE}` cu

        ON cu.ID_COMPANY =
            c.ID_COMPANY

    JOIN `{BQ_PROJECT}.{BQ_DATASET}.RATECARD_UNIVERSE` u

        ON u.ID_UNIVERSE =
            cu.ID_UNIVERSE

    JOIN `{BQ_PROJECT}.{BQ_DATASET}.RATECARD_USER_UNIVERSE` uu

        ON uu.ID_UNIVERSE =
            cu.ID_UNIVERSE

    LEFT JOIN (

        SELECT

            company.id_company
                AS ID_COMPANY,

            COUNT(
                DISTINCT content.ID_CONTENT
            ) AS CONTENT_COUNT

        FROM `{TABLE_CONTENT_ENRICHED}` content,

        UNNEST(
            content.COMPANIES
        ) company

        WHERE

            content.IS_ACTIVE = TRUE

            AND content.STATUS =
                "PUBLISHED"

        GROUP BY

            company.id_company

    ) cc

        ON cc.ID_COMPANY =
            c.ID_COMPANY

    WHERE

        c.IS_ACTIVE = TRUE

        AND uu.ID_USER =
            @user_id

    GROUP BY

        c.ID_COMPANY,

        c.NAME,

        c.TYPE,

        c.IS_PARTNER,

        c.MEDIA_LOGO_RECTANGLE_ID,

        cc.CONTENT_COUNT

    ORDER BY

        UPPER(
            c.NAME
        )
    """

    rows = query_bq(
        sql,
        {
            "user_id":
                user_id,
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
        ).append(
            {
                "alias":
                    row["ALIAS"],
            }
        )

    return [

        {

            "id_company":
                row["ID_COMPANY"],

            "name":
                row["NAME"],

            "type":
                row.get(
                    "TYPE",
                ),

            "is_partner":
                row["IS_PARTNER"],

            "media_logo_rectangle_id":
                row.get(
                    "MEDIA_LOGO_RECTANGLE_ID",
                ),

            "content_count":
                row.get(
                    "CONTENT_COUNT",
                    0,
                ),

            "aliases":
                aliases_map.get(
                    row["ID_COMPANY"],
                    [],
                ),

            "universes":
                row.get(
                    "UNIVERSES",
                )
                or [],

        }

        for row in rows

    ]
