import uuid

from config import BQ_PROJECT, BQ_DATASET
from utils.bigquery_utils import query_bq
from typing import Optional, Dict, Any, List


# =========================================================
# TABLES
# =========================================================

TABLE_USER = f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_USER"
TABLE_USER_UNIVERSE = f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_USER_UNIVERSE"
TABLE_SOURCE_UNIVERSE = f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_SOURCE_UNIVERSE"

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

    universe_ids = [u["ID_UNIVERSE"] for u in universes] if universes else []

    # ============================================================
    # RETURN SAFE
    # ============================================================

    return {
        "user_id": user.get("ID_USER"),
        "email": user.get("EMAIL"),
        "name": user.get("NAME"),
        "company": user.get("COMPANY"),
        "lang": user.get("LANGUAGE") or "fr",  # 🔥 fallback langue
        "role": user.get("ROLE") or "user",
        "universes": universe_ids,
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

    SUPPORTED_LANGS = ["fr", "en"]

    language = (
        payload.language
        if payload.language in SUPPORTED_LANGS
        else "fr"
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
        },
    )

    # --------------------------------------------------------
    # ASSIGN UNIVERS
    # --------------------------------------------------------

    assign_universes(user_id, payload.universes)

    return user_id


# =========================================================
# UPDATE USER
# =========================================================

def update_user(payload):
    user = get_user_by_id(payload.user_id)

    if not user:
        raise ValueError("User not found")

    query_bq(
        f"""
        UPDATE `{TABLE_USER}`
        SET
            NAME = @name,
            COMPANY = @company,
            LANGUAGE = @language,
            ROLE = COALESCE(@role, ROLE)
        WHERE ID_USER = @user_id
        """,
        {
            "user_id": payload.user_id,
            "name": payload.name,
            "company": payload.company,
            "language": payload.language or "fr",
            "role": payload.role,
        },
    )

    assign_universes(payload.user_id, payload.universes)


# =========================================================
# LIST USERS
# =========================================================

def list_users():
    query = f"""
    SELECT
        ID_USER,
        EMAIL,
        NAME,
        COMPANY,
        LANGUAGE,
        ROLE,
        CREATED_AT
    FROM `{TABLE_USER}`
    ORDER BY CREATED_AT DESC
    """

    return query_bq(query)

# =========================================================
# LIST DIGEST USERS
# =========================================================

def list_digest_users():

    table_digest_send = (
        f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_DIGEST_SEND"
    )

    table_user_preferences = (
        f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_USER_PREFERENCES"
    )

    query = f"""

    SELECT DISTINCT

        u.ID_USER,
        u.EMAIL,
        u.NAME,
        u.COMPANY,
        u.LANGUAGE,
        u.ROLE,
        u.CREATED_AT,

        ds.LAST_SENT_AT

    FROM `{TABLE_USER}` u

    # =====================================================
    # ONLY USERS WITH PREFERENCES
    # =====================================================

    INNER JOIN `{table_user_preferences}` p

    ON u.ID_USER = p.ID_USER

    # =====================================================
    # LAST DIGEST SENT
    # =====================================================

    LEFT JOIN (

        SELECT
            ID_USER,

            MAX(SENT_AT) AS LAST_SENT_AT

        FROM `{table_digest_send}`

        GROUP BY ID_USER

    ) ds

    ON u.ID_USER = ds.ID_USER

    # =====================================================
    # ORDER
    # =====================================================

    ORDER BY
        ds.LAST_SENT_AT DESC NULLS LAST,
        u.CREATED_AT DESC

    """

    return query_bq(
        query
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
