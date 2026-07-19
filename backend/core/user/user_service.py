import uuid

from config import BQ_PROJECT, BQ_DATASET
from utils.bigquery_utils import query_bq
from typing import Optional, Dict, Any, List

from core.user.user_keyword_service import (
    get_user_keywords,
)

from core.user.user_profile_service import (
    get_user_profile,
)


# =========================================================
# TABLES
# =========================================================

TABLE_USER = f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_USER"
TABLE_USER_UNIVERSE = f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_USER_UNIVERSE"
TABLE_SOURCE_UNIVERSE = f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_SOURCE_UNIVERSE"
TABLE_USER_KEYWORD = f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_USER_KEYWORD"

SUPPORTED_LANGS = ["fr", "en"]


# =========================================================
# GET USER
# =========================================================

def get_user_by_email(email: str):
    query = f"""
    SELECT *
    FROM `{TABLE_USER}`
    WHERE EMAIL = @email
    LIMIT 1
    """

    rows = query_bq(query, {"email": email})
    return rows[0] if rows else None


def get_user_by_id(user_id: str):
    query = f"""
    SELECT *
    FROM `{TABLE_USER}`
    WHERE ID_USER = @user_id
    LIMIT 1
    """

    rows = query_bq(query, {"user_id": user_id})
    return rows[0] if rows else None


# =========================================================
# UNIVERS
# =========================================================

def get_user_universes(user_id: str):
    query = f"""
    SELECT ID_UNIVERSE
    FROM `{TABLE_USER_UNIVERSE}`
    WHERE ID_USER = @user_id
    """

    rows = query_bq(query, {"user_id": user_id})
    return [row["ID_UNIVERSE"] for row in rows]


def get_sources_from_universes(universes: list[str]):
    if not universes:
        return []

    query = f"""
    SELECT DISTINCT ID_SOURCE
    FROM `{TABLE_SOURCE_UNIVERSE}`
    WHERE ID_UNIVERSE IN UNNEST(@universes)
    """

    rows = query_bq(query, {"universes": universes})
    return [row["ID_SOURCE"] for row in rows]

# =========================================================
# USER CONTEXT
# =========================================================

def get_user_context(user_id: str) -> Optional[Dict]:

    if not user_id:
        return None

    # ============================================================
    # USER
    # ============================================================

    rows = query_bq(
        f"""
        SELECT
            ID_USER,
            EMAIL,
            NAME,
            COMPANY,
            LANGUAGE,
            ROLE
        FROM `{TABLE_USER}`
        WHERE ID_USER = @user_id
        LIMIT 1
        """,
        {"user_id": user_id}
    )

    if not rows:
        # 🔥 USER INEXISTANT → on ne casse pas
        return None

    user = rows[0]

    # ============================================================
    # UNIVERS (OPTIONNEL)
    # ============================================================

    universes = query_bq(
        f"""
        SELECT ID_UNIVERSE
        FROM `{TABLE_USER_UNIVERSE}`
        WHERE ID_USER = @user_id
        """,
        {"user_id": user_id}
    )

    universe_ids = (
        [u["ID_UNIVERSE"] for u in universes]
        if universes
        else []
    )

    # ============================================================
    # KEYWORDS
    # ============================================================

    try:
        keywords = get_user_keywords(user_id)
    except Exception:
        keywords = []

    # ============================================================
    # PROFILE
    # ============================================================

    try:
        profile = get_user_profile(user_id)
    except Exception:
        profile = None

    # ============================================================
    # RETURN SAFE
    # ============================================================

    return {
        "user_id": user.get("ID_USER"),
        "email": user.get("EMAIL"),
        "name": user.get("NAME"),
        "company": user.get("COMPANY"),

        "lang": user.get("LANGUAGE") or "fr",
        "role": user.get("ROLE") or "user",

        "universes": universe_ids,

        # NEW
        "keywords": keywords or [],

        # NEW
        "profile": profile or {
            "geography_1": None,
            "geography_2": None,
            "geography_3": None,
            "profile_text": None,
        },
    }


# =========================================================
# CREATE USER (SIMPLE)
# =========================================================

def create_user(payload):
    existing = query_bq(
        f"""
        SELECT ID_USER
        FROM `{TABLE_USER}`
        WHERE EMAIL = @email
        LIMIT 1
        """,
        {"email": payload.email},
    )

    if existing:
        raise ValueError("User already exists")

    if not payload.password:
        raise ValueError("Password is required")

    # --------------------------------------------------------
    # LANGUAGE HANDLING (SECURE)
    # --------------------------------------------------------

    language = (
        payload.language
        if payload.language in SUPPORTED_LANGS
        else "fr"
    )

    # --------------------------------------------------------
    # DEFAULTS
    # --------------------------------------------------------

    profile_type = payload.profile_type or "USER"

    display_name = (
        payload.display_name
        or payload.name
        or payload.email
    )

    description = payload.description

    frequency = (
        payload.frequency
        or "WEEKLY"
    )

    is_active = (
        True
        if payload.is_active is None
        else payload.is_active
    )

    # --------------------------------------------------------
    # CREATE USER
    # --------------------------------------------------------

    user_id = str(uuid.uuid4())

    query_bq(
        f"""
        INSERT INTO `{TABLE_USER}` (
            ID_USER,
            EMAIL,
            PASSWORD,
            NAME,
            COMPANY,
            LANGUAGE,
            ROLE,
            PROFILE_TYPE,
            DISPLAY_NAME,
            DESCRIPTION,
            FREQUENCY,
            IS_ACTIVE,
            CREATED_AT
        )
        VALUES (
            @id_user,
            @email,
            @password,
            @name,
            @company,
            @language,
            @role,
            @profile_type,
            @display_name,
            @description,
            @frequency,
            @is_active,
            CURRENT_TIMESTAMP()
        )
        """,
        {
            "id_user": user_id,
            "email": payload.email,
            "password": payload.password,
            "name": payload.name,
            "company": payload.company,
            "language": language,
            "role": payload.role or "user",
            "profile_type": profile_type,
            "display_name": display_name,
            "description": description,
            "frequency": frequency,
            "is_active": is_active,
        },
    )

    # --------------------------------------------------------
    # ASSIGN UNIVERS
    # --------------------------------------------------------

    assign_universes(
        user_id,
        payload.universes or [],
    )

    return user_id


# =========================================================
# UPDATE USER
# =========================================================

# =========================================================
# UPDATE USER
# =========================================================

def update_user(payload):

    user = get_user_by_id(
        payload.user_id
    )

    if not user:
        raise ValueError(
            "User not found"
        )

    query_bq(
        f"""
        UPDATE `{TABLE_USER}`
        SET
            NAME = @name,
            COMPANY = @company,
            LANGUAGE = @language,
            ROLE = COALESCE(@role, ROLE),

            PROFILE_TYPE = COALESCE(
                @profile_type,
                PROFILE_TYPE
            ),

            DISPLAY_NAME = COALESCE(
                @display_name,
                DISPLAY_NAME
            ),

            DESCRIPTION = COALESCE(
                @description,
                DESCRIPTION
            ),

            FREQUENCY = COALESCE(
                @frequency,
                FREQUENCY
            ),

            IS_ACTIVE = COALESCE(
                @is_active,
                IS_ACTIVE
            )

        WHERE ID_USER = @user_id
        """,
        {
            "user_id": payload.user_id,
            "name": payload.name,
            "company": payload.company,
            "language": payload.language or "fr",
            "role": payload.role,

            "profile_type": payload.profile_type,
            "display_name": payload.display_name,
            "description": payload.description,
            "frequency": payload.frequency,
            "is_active": payload.is_active,
        },
    )

    # =====================================================
    # UNIVERS (OPTIONAL)
    # =====================================================

    if payload.universes is not None:

        assign_universes(
            payload.user_id,
            payload.universes,
        )

# =========================================================
# LIST USERS
# =========================================================

def list_users(
    profile_type: Optional[str] = None,
):

    where_clause = ""

    params = {}

    if profile_type:
        where_clause = """
        WHERE u.PROFILE_TYPE = @profile_type
        """
        params["profile_type"] = profile_type

    query = f"""
    SELECT

        u.ID_USER,
        u.EMAIL,
        u.NAME,
        u.DISPLAY_NAME,
        u.COMPANY,
        u.LANGUAGE,
        u.ROLE,
        u.PROFILE_TYPE,
        u.FREQUENCY,
        u.IS_ACTIVE,
        u.CREATED_AT,

        COUNT(DISTINCT k.KEYWORD)
            AS KEYWORDS_COUNT,

        MAX(
            p.GEOGRAPHY_1
        ) AS GEOGRAPHY_1,

        MAX(
            CASE
                WHEN p.PROFILE_TEXT IS NOT NULL
                 AND TRIM(p.PROFILE_TEXT) != ''
                THEN TRUE
                ELSE FALSE
            END
        ) AS HAS_PROFILE

    FROM `{TABLE_USER}` u

    LEFT JOIN `{BQ_PROJECT}.{BQ_DATASET}.RATECARD_USER_KEYWORD` k
      ON u.ID_USER = k.ID_USER

    LEFT JOIN `{BQ_PROJECT}.{BQ_DATASET}.RATECARD_USER_PROFILE` p
      ON u.ID_USER = p.ID_USER

    {where_clause}

    GROUP BY
        u.ID_USER,
        u.EMAIL,
        u.NAME,
        u.DISPLAY_NAME,
        u.COMPANY,
        u.LANGUAGE,
        u.ROLE,
        u.PROFILE_TYPE,
        u.FREQUENCY,
        u.IS_ACTIVE,
        u.CREATED_AT

    ORDER BY
        u.CREATED_AT DESC
    """

    return query_bq(
        query,
        params,
    )


# =========================================================
# LIST DIGEST PROFILES
# =========================================================

def list_digest_users(
    profile_type: str = "USER",
):

    table_digest_send = (
        f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_DIGEST_SEND"
    )

    table_user_preferences = (
        f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_USER_PREFERENCES"
    )

    table_user_keyword = (
        f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_USER_KEYWORD"
    )

    query = f"""

    SELECT DISTINCT

        u.ID_USER,
        u.EMAIL,
        u.NAME,
        u.DISPLAY_NAME,
        u.COMPANY,
        u.LANGUAGE,
        u.ROLE,
        u.PROFILE_TYPE,
        u.FREQUENCY,
        u.CREATED_AT,

        ds.LAST_SENT_AT

    FROM `{TABLE_USER}` u

    LEFT JOIN (

        SELECT
            ID_USER,
            MAX(SENT_AT) AS LAST_SENT_AT

        FROM `{table_digest_send}`

        GROUP BY ID_USER

    ) ds

        ON u.ID_USER = ds.ID_USER

    WHERE

        u.PROFILE_TYPE = @profile_type

        AND (

            EXISTS (

                SELECT 1

                FROM `{table_user_preferences}` p

                WHERE p.ID_USER = u.ID_USER

            )

            OR

            EXISTS (

                SELECT 1

                FROM `{table_user_keyword}` k

                WHERE k.ID_USER = u.ID_USER

            )

        )

    ORDER BY
        ds.LAST_SENT_AT DESC NULLS LAST,
        u.CREATED_AT DESC

    """

    return query_bq(
        query,
        {
            "profile_type": profile_type,
        },
    )

# =========================================================
# ASSIGN UNIVERS
# =========================================================

def assign_universes(user_id: str, universes: list[str]):
    query_bq(
        f"""
        DELETE FROM `{TABLE_USER_UNIVERSE}`
        WHERE ID_USER = @user_id
        """,
        {"user_id": user_id},
    )

    for u in universes:
        query_bq(
            f"""
            INSERT INTO `{TABLE_USER_UNIVERSE}` (
                ID_USER,
                ID_UNIVERSE,
                CREATED_AT
            )
            VALUES (
                @user_id,
                @universe,
                CURRENT_TIMESTAMP()
            )
            """,
            {
                "user_id": user_id,
                "universe": u,
            },
        )
