from typing import (
    List,
    Dict,
    Optional,
)

from config import (
    BQ_PROJECT,
    BQ_DATASET,
)

from utils.bigquery_utils import (
    query_bq,
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

TABLE_COMPANY_UNIVERSE = (
    f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_COMPANY_UNIVERSE"
)

TABLE_USER_UNIVERSE = (
    f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_USER_UNIVERSE"
)

TABLE_CONTENT_ENRICHED = (
    f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_CONTENT_ENRICHED"
)


# ============================================================
# PUBLIC VIEW
# ============================================================

def get_solution_view(
    solution_id: str,
) -> Optional[Dict]:

    rows = query_bq(
        f"""
        SELECT

            s.ID_SOLUTION,

            s.NAME,

            c.NAME AS COMPANY_NAME,

            s.MEDIA_LOGO_RECTANGLE_ID
                AS SOLUTION_LOGO,

            c.MEDIA_LOGO_RECTANGLE_ID
                AS COMPANY_LOGO

        FROM `{TABLE_SOLUTION}` s

        LEFT JOIN `{TABLE_COMPANY}` c

            ON c.ID_COMPANY =
                s.ID_COMPANY

        WHERE

            s.ID_SOLUTION =
                @solution_id

        LIMIT 1
        """,
        {
            "solution_id":
                solution_id,
        },
    )

    if not rows:

        return None

    solution = rows[0]

    solution_logo = (
        solution.get(
            "SOLUTION_LOGO"
        )
    )

    company_logo = (
        solution.get(
            "COMPANY_LOGO"
        )
    )

    return {

        "id_solution":
            solution.get(
                "ID_SOLUTION",
            ),

        "name":
            solution.get(
                "NAME",
            ),

        "company_name":
            solution.get(
                "COMPANY_NAME",
            ),

        "media_logo_rectangle_id":
            (
                solution_logo
                or company_logo
            ),

        "logo_type":
            (
                "solution"
                if solution_logo
                else "company"
            ),

    }


# ============================================================
# LIST CURATOR
# ============================================================

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

            c.MEDIA_LOGO_RECTANGLE_ID
                AS COMPANY_LOGO,

            CAST(
                c.IS_PARTNER AS BOOL
            ) AS IS_PARTNER,

            s.CREATED_AT,

            s.UPDATED_AT,

            COALESCE(
                sc.CONTENT_COUNT,
                0
            ) AS CONTENT_COUNT,

            ARRAY_AGG(
                DISTINCT u.LABEL
                IGNORE NULLS
            ) AS UNIVERSES

        FROM `{TABLE_SOLUTION}` s

        JOIN `{TABLE_COMPANY}` c

            ON c.ID_COMPANY =
                s.ID_COMPANY

        JOIN `{TABLE_COMPANY_UNIVERSE}` cu

            ON cu.ID_COMPANY =
                c.ID_COMPANY

        JOIN `{BQ_PROJECT}.{BQ_DATASET}.RATECARD_UNIVERSE` u

            ON u.ID_UNIVERSE =
                cu.ID_UNIVERSE

        JOIN `{TABLE_USER_UNIVERSE}` uu

            ON uu.ID_UNIVERSE =
                cu.ID_UNIVERSE

        LEFT JOIN (

            SELECT

                solution.id_solution
                    AS ID_SOLUTION,

                COUNT(
                    DISTINCT content.ID_CONTENT
                ) AS CONTENT_COUNT

            FROM `{TABLE_CONTENT_ENRICHED}` content,

            UNNEST(
                content.SOLUTIONS
            ) solution

            WHERE

                content.IS_ACTIVE = TRUE

                AND content.STATUS =
                    "PUBLISHED"

            GROUP BY

                solution.id_solution

        ) sc

            ON sc.ID_SOLUTION =
                s.ID_SOLUTION

        WHERE

            s.IS_ACTIVE = TRUE

            AND uu.ID_USER =
                @user_id

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

            sc.CONTENT_COUNT

        ORDER BY

            UPPER(
                s.NAME
            )
        """,
        {
            "user_id":
                user_id,
        },
    )

    return [

        {

            "id_solution":
                row["ID_SOLUTION"],

            "name":
                row["NAME"],

            "id_company":
                row["ID_COMPANY"],

            "company_name":
                row.get(
                    "COMPANY_NAME",
                ),

            "media_logo_rectangle_id":
                (
                    row.get(
                        "SOLUTION_LOGO",
                    )
                    or row.get(
                        "COMPANY_LOGO",
                    )
                ),

            "logo_type":
                (
                    "solution"
                    if row.get(
                        "SOLUTION_LOGO",
                    )
                    else "company"
                ),

            "is_partner":
                row.get(
                    "IS_PARTNER",
                    False,
                ),

            "created_at":
                row.get(
                    "CREATED_AT",
                ),

            "updated_at":
                row.get(
                    "UPDATED_AT",
                ),

            "content_count":
                row.get(
                    "CONTENT_COUNT",
                    0,
                ),

            "universes":
                (
                    row.get(
                        "UNIVERSES",
                    )
                    or []
                ),

        }

        for row in rows

    ]
