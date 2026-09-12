import json

from typing import (
    Any,
    Dict,
    Optional,
)

from config import (
    BQ_PROJECT,
    BQ_DATASET,
)

from core.user.profile_models import (
    ProfileTransformerResult,
)

from utils.bigquery_utils import (
    query_bq,
)


TABLE_USER_PROFILE = (
    f"{BQ_PROJECT}.{BQ_DATASET}."
    "RATECARD_USER_PROFILE"
)


# ============================================================
# PARSE STRUCTURED PROFILE
# ============================================================

def parse_structured_profile(
    value: Optional[str],
) -> Optional[Dict[str, Any]]:

    if not value:

        return None

    try:

        parsed = json.loads(
            value
        )

    except (
        TypeError,
        json.JSONDecodeError,
    ):

        return None

    if not isinstance(
        parsed,
        dict,
    ):

        return None

    return parsed


# ============================================================
# GET USER PROFILE
# ============================================================

def get_user_profile(
    user_id: str,
) -> Optional[Dict[str, Any]]:

    rows = query_bq(
        f"""
        SELECT
            GEOGRAPHY_1,
            GEOGRAPHY_2,
            GEOGRAPHY_3,
            PROFILE_TEXT,
            PROFILE_STRUCTURED_JSON,
            PROFILE_SOURCE_HASH,
            PROFILE_SCHEMA_VERSION,
            PROFILE_TRANSFORMER_VERSION,
            PROFILE_STRUCTURED_AT,
            PROFILE_STRUCTURED_STATUS,
            PROFILE_STRUCTURED_ERROR
        FROM `{TABLE_USER_PROFILE}`
        WHERE ID_USER = @user_id
        LIMIT 1
        """,
        {
            "user_id_id": user_id,
        },
    )

    if not rows:

        return None

    row = rows[0]

    structured_profile = (
        parse_structured_profile(
            row.get(
                "PROFILE_STRUCTURED_JSON"
            )
        )
    )

    return {
        "geography_1": row.get(
            "GEOGRAPHY_1"
        ),
        "geography_2": row.get(
            "GEOGRAPHY_2"
        ),
        "geography_3": row.get(
            "GEOGRAPHY_3"
        ),
        "profile_text": row.get(
            "PROFILE_TEXT"
        ),
        "structured_profile": (
            structured_profile
        ),
        "profile_source_hash": row.get(
            "PROFILE_SOURCE_HASH"
        ),
        "profile_schema_version": row.get(
            "PROFILE_SCHEMA_VERSION"
        ),
        "profile_transformer_version": row.get(
            "PROFILE_TRANSFORMER_VERSION"
        ),
        "profile_structured_at": row.get(
            "PROFILE_STRUCTURED_AT"
        ),
        "profile_structured_status": row.get(
            "PROFILE_STRUCTURED_STATUS"
        ),
        "profile_structured_error": row.get(
            "PROFILE_STRUCTURED_ERROR"
        ),
    }


# ============================================================
# GET PROFILE SOURCE HASH
# ============================================================

def get_profile_source_hash(
    user_id: str,
) -> Optional[str]:

    rows = query_bq(
        f"""
        SELECT
            PROFILE_SOURCE_HASH
        FROM `{TABLE_USER_PROFILE}`
        WHERE ID_USER = @user_id
        LIMIT 1
        """,
        {
            "user_id": user_id,
        },
    )

    if not rows:

        return None

    return rows[0].get(
        "PROFILE_SOURCE_HASH"
    )


# ============================================================
# CHECK SOURCE CHANGE
# ============================================================

def has_profile_source_changed(
    user_id: str,
    source_hash: str,
) -> bool:

    current_hash = get_profile_source_hash(
        user_id=user_id,
    )

    return (
        current_hash
        != source_hash
    )


# ============================================================
# UPDATE RAW USER PROFILE
# ============================================================

def update_user_profile(
    user_id: str,
    geography_1: Optional[str] = None,
    geography_2: Optional[str] = None,
    geography_3: Optional[str] = None,
    profile_text: Optional[str] = None,
) -> None:

    query_bq(
        f"""
        MERGE `{TABLE_USER_PROFILE}` AS target

        USING (
            SELECT
                @user_id AS ID_USER,
                @geography_1 AS GEOGRAPHY_1,
                @geography_2 AS GEOGRAPHY_2,
                @geography_3 AS GEOGRAPHY_3,
                @profile_text AS PROFILE_TEXT
        ) AS source

        ON target.ID_USER = source.ID_USER

        WHEN MATCHED THEN
            UPDATE SET
                GEOGRAPHY_1 =
                    source.GEOGRAPHY_1,

                GEOGRAPHY_2 =
                    source.GEOGRAPHY_2,

                GEOGRAPHY_3 =
                    source.GEOGRAPHY_3,

                PROFILE_TEXT =
                    source.PROFILE_TEXT,

                PROFILE_STRUCTURED_STATUS =
                    CASE
                        WHEN target.PROFILE_STRUCTURED_JSON
                            IS NULL
                        THEN NULL
                        ELSE 'STALE'
                    END,

                PROFILE_STRUCTURED_ERROR =
                    NULL

        WHEN NOT MATCHED THEN
            INSERT (
                ID_USER,
                GEOGRAPHY_1,
                GEOGRAPHY_2,
                GEOGRAPHY_3,
                PROFILE_TEXT,
                PROFILE_STRUCTURED_STATUS
            )
            VALUES (
                source.ID_USER,
                source.GEOGRAPHY_1,
                source.GEOGRAPHY_2,
                source.GEOGRAPHY_3,
                source.PROFILE_TEXT,
                NULL
            )
        """,
        {
            "user_id": user_id,
            "geography_1": geography_1,
            "geography_2": geography_2,
            "geography_3": geography_3,
            "profile_text": profile_text,
        },
    )


# ============================================================
# SAVE VALIDATED USER PROFILE
# ============================================================

def save_validated_user_profile(
    user_id: str,
    geography_1: Optional[str],
    geography_2: Optional[str],
    geography_3: Optional[str],
    profile_text: str,
    transformer_result: ProfileTransformerResult,
) -> None:

    structured_json = (
        transformer_result
        .structured_profile
        .json(
            ensure_ascii=False,
        )
    )

    query_bq(
        f"""
        MERGE `{TABLE_USER_PROFILE}` AS target

        USING (
            SELECT
                @user_id AS ID_USER,
                @geography__COPY_1 AS GEOGRAPHY_1,
                @geography_2 AS GEOGRAPHY_2,
                @geography_3 AS GEOGRAPHY_3,
                @profile_text AS PROFILE_TEXT,
                @structured_json
                    AS PROFILE_STRUCTURED_JSON,
                @source_hash
                    AS PROFILE_SOURCE_HASH,
                @schema_version
                    AS PROFILE_SCHEMA_VERSION,
                @transformer_version
                    AS PROFILE_TRANSFORMER_VERSION
        ) AS source

        ON target.ID_USER = source.ID_USER

        WHEN MATCHED THEN
            UPDATE SET
                GEOGRAPHY_1 =
                    source.GEOGRAPHY_1,

                GEOGRAPHY_2 =
                    source.GEOGRAPHY_2,

                GEOGRAPHY_3 =
                    source.GEOGRAPHY_3,

                PROFILE_TEXT =
                    source.PROFILE_TEXT,

                PROFILE_STRUCTURED_JSON =
                    source.PROFILE_STRUCTURED_JSON,

                PROFILE_SOURCE_HASH =
                    source.PROFILE_SOURCE_HASH,

                PROFILE_SCHEMA_VERSION =
                    source.PROFILE_SCHEMA_VERSION,

                PROFILE_TRANSFORMER_VERSION =
                    source.PROFILE_TRANSFORMER_VERSION,

                PROFILE_STRUCTURED_AT =
                    CURRENT_TIMESTAMP(),

                PROFILE_STRUCTURED_STATUS =
                    'READY',

                PROFILE_STRUCTURED_ERROR =
                    NULL

        WHEN NOT MATCHED THEN
            INSERT (
                ID_USER,
                GEOGRAPHY_1,
                GEOGRAPHY_2,
                GEOGRAPHY_3TITLE_3,
                PROFILE_TEXT,
                PROFILE_STRUCTURED_JSON,
                PROFILE_SOURCE_HASH,
                PROFILE_SCHEMA_VERSION,
                PROFILE_TRANSFORMER_VERSION,
                PROFILE_STRUCTURED_AT,
                PROFILE_STRUCTURED_STATUS,
                PROFILE_STRUCTURED_ERROR
            )
            VALUES (
                source.ID_USER,
                source.GEOGRAPHY_1,
                source.GEOGRAPHY_2,
                source.GEOGRAPHY_3,
                source.PROFILE_TEXT,
                source.PROFILE_STRUCTURED_JSON,
                source.PROFILE_SOURCE_HASH,
                source.PROFILE_SCHEMA_VERSION,
                source.PROFILE_TRANSFORMER_VERSION,
                CURRENT_TIMESTAMP(),
                'READY',
                NULL
            )
        """,
        {
            "user_id": user_id,
            "geography_1": geography_1,
            "geography_2": geography_2,
            "geography_3": geography_3,
            "profile_text": profile_text,
            "structured_json": (
                structured_json
            ),
            "source_hash": (
                transformer_result
                .source_hash
            ),
            "schema_version": (
                transformer_result
                .schema_version
            ),
            "transformer_version": (
                transformer_result
                .transformer_version
            ),
        },
    )


# ============================================================
# RECORD TRANSFORMATION ERROR
# ============================================================

def record_profile_transformation_error(
    user_id: str,
    error: str,
) -> None:

    query_bq(
        f"""
        UPDATE `{TABLE_USER_PROFILE}`
        SET
            PROFILE_STRUCTURED_STATUS =
                CASE
                    WHEN PROFILE_STRUCTURED_JSON IS NULL
                    THEN 'ERROR'
                    ELSE PROFILE_STRUCTURED_STATUS
                END,

            PROFILE_STRUCTURED_ERROR =
                @error

        WHERE ID_USER = @user_id
        """,
        {
            "user_id": user_id,
            "error": error[
                :4000
            ],
        },
    )
