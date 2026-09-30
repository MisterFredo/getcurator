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


# ============================================================
# TABLE
# ============================================================

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

            PROFILE_EDITORIAL_TEXT,
            PROFILE_EDITORIAL_SOURCE_HASH,
            PROFILE_EDITORIAL_TRANSFORMER_VERSION,
            PROFILE_EDITORIAL_AT,
            PROFILE_EDITORIAL_STATUS,
            PROFILE_EDITORIAL_ERROR,

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
            "user_id":
                user_id,
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

        "geography_1":
            row.get(
                "GEOGRAPHY_1"
            ),

        "geography_2":
            row.get(
                "GEOGRAPHY_2"
            ),

        "geography_3":
            row.get(
                "GEOGRAPHY_3"
            ),

        # Human-readable profile.
        # This is the version displayed publicly.
        "profile_text":
            row.get(
                "PROFILE_TEXT"
            ),

        # Extended editorial profile.
        # This is not intended for public display.
        "profile_editorial_text":
            row.get(
                "PROFILE_EDITORIAL_TEXT"
            ),

        "profile_editorial_source_hash":
            row.get(
                "PROFILE_EDITORIAL_SOURCE_HASH"
            ),

        "profile_editorial_transformer_version":
            row.get(
                "PROFILE_EDITORIAL_TRANSFORMER_VERSION"
            ),

        "profile_editorial_at":
            row.get(
                "PROFILE_EDITORIAL_AT"
            ),

        "profile_editorial_status":
            row.get(
                "PROFILE_EDITORIAL_STATUS"
            ),

        "profile_editorial_error":
            row.get(
                "PROFILE_EDITORIAL_ERROR"
            ),

        # Structured machine profile.
        "structured_profile":
            structured_profile,

        "profile_source_hash":
            row.get(
                "PROFILE_SOURCE_HASH"
            ),

        "profile_schema_version":
            row.get(
                "PROFILE_SCHEMA_VERSION"
            ),

        "profile_transformer_version":
            row.get(
                "PROFILE_TRANSFORMER_VERSION"
            ),

        "profile_structured_at":
            row.get(
                "PROFILE_STRUCTURED_AT"
            ),

        "profile_structured_status":
            row.get(
                "PROFILE_STRUCTURED_STATUS"
            ),

        "profile_structured_error":
            row.get(
                "PROFILE_STRUCTURED_ERROR"
            ),

    }


# ============================================================
# GET EDITORIAL SOURCE HASH
# ============================================================

def get_profile_editorial_source_hash(
    user_id: str,
) -> Optional[str]:

    rows = query_bq(
        f"""
        SELECT

            PROFILE_EDITORIAL_SOURCE_HASH

        FROM `{TABLE_USER_PROFILE}`

        WHERE ID_USER = @user_id

        LIMIT 1
        """,
        {
            "user_id":
                user_id,
        },
    )

    if not rows:

        return None

    return rows[0].get(
        "PROFILE_EDITORIAL_SOURCE_HASH"
    )


# ============================================================
# CHECK EDITORIAL SOURCE CHANGE
# ============================================================

def has_profile_editorial_source_changed(
    user_id: str,
    source_hash: str,
) -> bool:

    current_hash = (
        get_profile_editorial_source_hash(
            user_id=user_id,
        )
    )

    return (
        current_hash
        != source_hash
    )


# ============================================================
# GET STRUCTURED SOURCE HASH
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
            "user_id":
                user_id,
        },
    )

    if not rows:

        return None

    return rows[0].get(
        "PROFILE_SOURCE_HASH"
    )


# ============================================================
# CHECK STRUCTURED SOURCE CHANGE
# ============================================================

def has_profile_source_changed(
    user_id: str,
    source_hash: str,
) -> bool:

    current_hash = (
        get_profile_source_hash(
            user_id=user_id,
        )
    )

    return (
        current_hash
        != source_hash
    )


# ============================================================
# UPDATE HUMAN-READABLE USER PROFILE
# ============================================================

def update_user_profile(
    user_id: str,
    geography_1: Optional[str] = None,
    geography_2: Optional[str] = None,
    geography_3: Optional[str] = None,
    profile_text: Optional[str] = None,
) -> None:
    """
    Save the human-readable profile.

    Any modification to this source invalidates both:

    - the extended editorial profile;
    - the structured machine profile.

    Existing generated values are preserved until the refreshed
    versions have been generated successfully.
    """

    query_bq(
        f"""
        MERGE `{TABLE_USER_PROFILE}` AS target

        USING (

            SELECT

                @user_id
                    AS ID_USER,

                @geography_1
                    AS GEOGRAPHY_1,

                @geography_2
                    AS GEOGRAPHY_2,

                @geography_3
                    AS GEOGRAPHY_3,

                @profile_text
                    AS PROFILE_TEXT

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

                PROFILE_EDITORIAL_STATUS =
                    CASE

                        WHEN target.PROFILE_EDITORIAL_TEXT
                            IS NULL

                        THEN NULL

                        ELSE 'STALE'

                    END,

                PROFILE_EDITORIAL_ERROR =
                    NULL,

                PROFILE_STRUCTURED_STATUS =
                    CASE

                        WHEN target.PROFILE_STRUCTURED_JSON
                            IS NULL

                        THEN NULL

                        ELSE 'STALE'

                    END,

                PROFILE_STRUCTURED_ERROR =
                    NULL,

                UPDATED_AT =
                    CURRENT_TIMESTAMP()

        WHEN NOT MATCHED THEN

            INSERT (

                ID_USER,

                GEOGRAPHY_1,
                GEOGRAPHY_2,
                GEOGRAPHY_3,

                PROFILE_TEXT,

                PROFILE_EDITORIAL_STATUS,
                PROFILE_STRUCTURED_STATUS,

                CREATED_AT,
                UPDATED_AT

            )

            VALUES (

                source.ID_USER,

                source.GEOGRAPHY_1,
                source.GEOGRAPHY_2,
                source.GEOGRAPHY_3,

                source.PROFILE_TEXT,

                NULL,
                NULL,

                CURRENT_TIMESTAMP(),
                CURRENT_TIMESTAMP()

            )
        """,
        {
            "user_id":
                user_id,

            "geography_1":
                geography_1,

            "geography_2":
                geography_2,

            "geography_3":
                geography_3,

            "profile_text":
                profile_text,
        },
    )


# ============================================================
# MARK EDITORIAL TRANSFORMATION AS BUILDING
# ============================================================

def mark_profile_editorial_building(
    user_id: str,
) -> None:

    query_bq(
        f"""
        UPDATE `{TABLE_USER_PROFILE}`

        SET

            PROFILE_EDITORIAL_STATUS =
                'BUILDING',

            PROFILE_EDITORIAL_ERROR =
                NULL,

            UPDATED_AT =
                CURRENT_TIMESTAMP()

        WHERE ID_USER = @user_id
        """,
        {
            "user_id":
                user_id,
        },
    )


# ============================================================
# SAVE EDITORIAL USER PROFILE
# ============================================================

def save_editorial_user_profile(
    user_id: str,
    editorial_text: str,
    source_hash: str,
    transformer_version: str,
) -> None:
    """
    Save the extended editorial profile.

    Saving a new editorial profile invalidates the structured
    machine profile, while preserving its existing JSON until
    the next structured transformation succeeds.
    """

    query_bq(
        f"""
        MERGE `{TABLE_USER_PROFILE}` AS target

        USING (

            SELECT

                @user_id
                    AS ID_USER,

                @editorial_text
                    AS PROFILE_EDITORIAL_TEXT,

                @source_hash
                    AS PROFILE_EDITORIAL_SOURCE_HASH,

                @transformer_version
                    AS PROFILE_EDITORIAL_TRANSFORMER_VERSION

        ) AS source

        ON target.ID_USER = source.ID_USER

        WHEN MATCHED THEN

            UPDATE SET

                PROFILE_EDITORIAL_TEXT =
                    source.PROFILE_EDITORIAL_TEXT,

                PROFILE_EDITORIAL_SOURCE_HASH =
                    source.PROFILE_EDITORIAL_SOURCE_HASH,

                PROFILE_EDITORIAL_TRANSFORMER_VERSION =
                    source.PROFILE_EDITORIAL_TRANSFORMER_VERSION,

                PROFILE_EDITORIAL_AT =
                    CURRENT_TIMESTAMP(),

                PROFILE_EDITORIAL_STATUS =
                    'READY',

                PROFILE_EDITORIAL_ERROR =
                    NULL,

                PROFILE_STRUCTURED_STATUS =
                    CASE

                        WHEN target.PROFILE_STRUCTURED_JSON
                            IS NULL

                        THEN NULL

                        ELSE 'STALE'

                    END,

                PROFILE_STRUCTURED_ERROR =
                    NULL,

                UPDATED_AT =
                    CURRENT_TIMESTAMP()

        WHEN NOT MATCHED THEN

            INSERT (

                ID_USER,

                PROFILE_EDITORIAL_TEXT,
                PROFILE_EDITORIAL_SOURCE_HASH,
                PROFILE_EDITORIAL_TRANSFORMER_VERSION,
                PROFILE_EDITORIAL_AT,
                PROFILE_EDITORIAL_STATUS,
                PROFILE_EDITORIAL_ERROR,

                PROFILE_STRUCTURED_STATUS,

                CREATED_AT,
                UPDATED_AT

            )

            VALUES (

                source.ID_USER,

                source.PROFILE_EDITORIAL_TEXT,
                source.PROFILE_EDITORIAL_SOURCE_HASH,
                source.PROFILE_EDITORIAL_TRANSFORMER_VERSION,
                CURRENT_TIMESTAMP(),
                'READY',
                NULL,

                NULL,

                CURRENT_TIMESTAMP(),
                CURRENT_TIMESTAMP()

            )
        """,
        {
            "user_id":
                user_id,

            "editorial_text":
                editorial_text,

            "source_hash":
                source_hash,

            "transformer_version":
                transformer_version,
        },
    )


# ============================================================
# MARK STRUCTURED TRANSFORMATION AS BUILDING
# ============================================================

def mark_profile_structured_building(
    user_id: str,
) -> None:

    query_bq(
        f"""
        UPDATE `{TABLE_USER_PROFILE}`

        SET

            PROFILE_STRUCTURED_STATUS =
                'BUILDING',

            PROFILE_STRUCTURED_ERROR =
                NULL,

            UPDATED_AT =
                CURRENT_TIMESTAMP()

        WHERE ID_USER = @user_id
        """,
        {
            "user_id":
                user_id,
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
    """
    Save the public profile and a successfully generated
    structured profile.

    This signature remains compatible with the existing
    transformation workflow.

    Once the editorial transformer is connected,
    transformer_result.source_hash must represent the hash
    of PROFILE_EDITORIAL_TEXT rather than PROFILE_TEXT.
    """

    structured_json = (
        transformer_result
        .structured_profile
        .model_dump_json()
    )

    query_bq(
        f"""
        MERGE `{TABLE_USER_PROFILE}` AS target

        USING (

            SELECT

                @user_id
                    AS ID_USER,

                @geography_1
                    AS GEOGRAPHY_1,

                @geography_2
                    AS GEOGRAPHY_2,

                @geography_3
                    AS GEOGRAPHY_3,

                @profile_text
                    AS PROFILE_TEXT,

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
                    NULL,

                UPDATED_AT =
                    CURRENT_TIMESTAMP()

        WHEN NOT MATCHED THEN

            INSERT (

                ID_USER,

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
                PROFILE_STRUCTURED_ERROR,

                CREATED_AT,
                UPDATED_AT

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
                NULL,

                CURRENT_TIMESTAMP(),
                CURRENT_TIMESTAMP()

            )
        """,
        {
            "user_id":
                user_id,

            "geography_1":
                geography_1,

            "geography_2":
                geography_2,

            "geography_3":
                geography_3,

            "profile_text":
                profile_text,

            "structured_json":
                structured_json,

            "source_hash":
                (
                    transformer_result
                    .source_hash
                ),

            "schema_version":
                (
                    transformer_result
                    .schema_version
                ),

            "transformer_version":
                (
                    transformer_result
                    .transformer_version
                ),
        },
    )


# ============================================================
# RECORD EDITORIAL TRANSFORMATION ERROR
# ============================================================

def record_profile_editorial_transformation_error(
    user_id: str,
    error: str,
) -> None:

    query_bq(
        f"""
        UPDATE `{TABLE_USER_PROFILE}`

        SET

            PROFILE_EDITORIAL_STATUS =
                'ERROR',

            PROFILE_EDITORIAL_ERROR =
                @error,

            UPDATED_AT =
                CURRENT_TIMESTAMP()

        WHERE ID_USER = @user_id
        """,
        {
            "user_id":
                user_id,

            "error":
                error[
                    :4000
                ],
        },
    )


# ============================================================
# RECORD STRUCTURED TRANSFORMATION ERROR
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
                'ERROR',

            PROFILE_STRUCTURED_ERROR =
                @error,

            UPDATED_AT =
                CURRENT_TIMESTAMP()

        WHERE ID_USER = @user_id
        """,
        {
            "user_id":
                user_id,

            "error":
                error[
                    :4000
                ],
        },
    )
