# backend/core/expertise/profile_service.py

from config import (
    BQ_PROJECT,
    BQ_DATASET,
)

from utils.bigquery_utils import (
    query_bq,
)

from api.expertise.models import (
    ExpertisePreferences,
    ExpertiseProfile,
)


# ============================================================
# TABLES
# ============================================================

TABLE_USER = (
    f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_USER"
)

TABLE_USER_PROFILE = (
    f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_USER_PROFILE"
)

TABLE_USER_PREFERENCES = (
    f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_USER_PREFERENCES"
)

TABLE_USER_KEYWORD = (
    f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_USER_KEYWORD"
)


# ============================================================
# LOAD PROFILE
# ============================================================

def load_profile(
    user_id: str,
) -> ExpertiseProfile:

    rows = query_bq(
        f"""
        WITH preferences AS (

            SELECT

                ID_USER,

                ARRAY_AGG(
                    IF(
                        TYPE = "COMPANY",
                        VALUE_ID,
                        NULL
                    )
                    IGNORE NULLS
                ) AS COMPANIES,

                ARRAY_AGG(
                    IF(
                        TYPE = "SOLUTION",
                        VALUE_ID,
                        NULL
                    )
                    IGNORE NULLS
                ) AS SOLUTIONS,

                ARRAY_AGG(
                    IF(
                        TYPE = "TOPIC",
                        VALUE_ID,
                        NULL
                    )
                    IGNORE NULLS
                ) AS TOPICS

            FROM `{TABLE_USER_PREFERENCES}`

            WHERE ID_USER = @user_id

            GROUP BY ID_USER
        ),

        keywords AS (

            SELECT

                ID_USER,

                ARRAY_AGG(
                    KEYWORD
                    ORDER BY KEYWORD
                ) AS KEYWORDS

            FROM `{TABLE_USER_KEYWORD}`

            WHERE ID_USER = @user_id

            GROUP BY ID_USER
        )

        SELECT

            u.ID_USER,

            u.LANGUAGE,

            p.GEOGRAPHY_1,
            p.GEOGRAPHY_2,
            p.GEOGRAPHY_3,
            p.PROFILE_TEXT,

            COALESCE(
                pref.COMPANIES,
                []
            ) AS COMPANIES,

            COALESCE(
                pref.SOLUTIONS,
                []
            ) AS SOLUTIONS,

            COALESCE(
                pref.TOPICS,
                []
            ) AS TOPICS,

            COALESCE(
                k.KEYWORDS,
                []
            ) AS KEYWORDS

        FROM `{TABLE_USER}` u

        LEFT JOIN `{TABLE_USER_PROFILE}` p

            ON p.ID_USER = u.ID_USER

        LEFT JOIN preferences pref

            ON pref.ID_USER = u.ID_USER

        LEFT JOIN keywords k

            ON k.ID_USER = u.ID_USER

        WHERE

            u.ID_USER = @user_id

        LIMIT 1
        """,
        {
            "user_id": user_id,
        },
    )

    if not rows:

        return ExpertiseProfile(

            id=user_id,

            language="fr",

            preferences=ExpertisePreferences(
                companies=[],
                solutions=[],
                topics=[],
            ),

            keywords=[],

            geographies=[],

            profile_text="",
        )

    row = rows[0]

    # ========================================================
    # GEOGRAPHIES
    # ========================================================

    geographies = [

        geography

        for geography in (

            row.get(
                "GEOGRAPHY_1",
            ),

            row.get(
                "GEOGRAPHY_2",
            ),

            row.get(
                "GEOGRAPHY_3",
            ),

        )

        if geography

    ]

    # ========================================================
    # PROFILE
    # ========================================================

    return ExpertiseProfile(

        id=user_id,

        language=(
            row.get(
                "LANGUAGE",
            )
            or "fr"
        ).lower(),

        preferences=ExpertisePreferences(

            companies=(
                row.get(
                    "COMPANIES",
                )
                or []
            ),

            solutions=(
                row.get(
                    "SOLUTIONS",
                )
                or []
            ),

            topics=(
                row.get(
                    "TOPICS",
                )
                or []
            ),

        ),

        keywords=(
            row.get(
                "KEYWORDS",
            )
            or []
        ),

        geographies=geographies,

        profile_text=(
            row.get(
                "PROFILE_TEXT",
            )
            or ""
        ),

    )
