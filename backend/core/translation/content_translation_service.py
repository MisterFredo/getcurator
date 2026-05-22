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

from core.translation.service import (
    translate_text,
)

# ============================================================
# TABLE
# ============================================================

TABLE_CONTENT = (
    f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_CONTENT"
)

# ============================================================
# FIELD MAPPING
# ============================================================

FIELD_MAPPING = {

    "TITLE": {
        "source": "TITLE",
        "target": "TITLE_EN",
    },

    "EXCERPT": {
        "source": "EXCERPT",
        "target": "EXCERPT_EN",
    },
}

# ============================================================
# HELPERS
# ============================================================

def _get_target_column(
    field: str,
    target_lang: str,
) -> str:

    field = field.upper()

    if target_lang != "en":
        raise ValueError(
            f"Langue non supportée : {target_lang}"
        )

    if field not in FIELD_MAPPING:
        raise ValueError(
            f"Champ non supporté : {field}"
        )

    return FIELD_MAPPING[field]["target"]


def _get_source_column(
    field: str
) -> str:

    field = field.upper()

    if field not in FIELD_MAPPING:
        raise ValueError(
            f"Champ non supporté : {field}"
        )

    return FIELD_MAPPING[field]["source"]

# ============================================================
# TRANSLATE ONE CONTENT
# ============================================================

def translate_content_fields(
    content_id: str,
    target_lang: str = "en",
    fields: Optional[List[str]] = None,
) -> Dict:

    if not fields:
        fields = [
            "TITLE",
            "EXCERPT",
        ]

    # ========================================================
    # LOAD CONTENT
    # ========================================================

    rows = query_bq(
        f"""
        SELECT *
        FROM `{TABLE_CONTENT}`
        WHERE ID_CONTENT = @content_id
        LIMIT 1
        """,
        {
            "content_id": content_id
        }
    )

    if not rows:
        raise ValueError(
            "Content introuvable"
        )

    content = rows[0]

    updated_fields = {}

    # ========================================================
    # TRANSLATE
    # ========================================================

    for field in fields:

        source_col = _get_source_column(
            field
        )

        target_col = _get_target_column(
            field,
            target_lang,
        )

        source_value = (
            content.get(source_col)
            or ""
        ).strip()

        if not source_value:
            continue

        translated = translate_text(
            text=source_value,
            target_lang=target_lang,
        )

        query_bq(
            f"""
            UPDATE `{TABLE_CONTENT}`
            SET {target_col} = @translated
            WHERE ID_CONTENT = @content_id
            """,
            {
                "translated": translated,
                "content_id": content_id,
            }
        )

        updated_fields[target_col] = (
            translated
        )

    return {
        "content_id": content_id,
        "target_lang": target_lang,
        "updated_fields": updated_fields,
    }

# ============================================================
# TRANSLATE BATCH
# ============================================================

def translate_contents_batch(
    target_lang: str = "en",

    fields: Optional[List[str]] = None,

    limit: int = 10000,

    only_missing: bool = True,

    content_ids: Optional[
        List[str]
    ] = None,

    source_id: Optional[str] = None,

    content_type: Optional[str] = None,
) -> Dict:

    if not fields:
        fields = [
            "TITLE",
            "EXCERPT",
        ]

    # ========================================================
    # FILTERS
    # ========================================================

    where_clauses = [
        "1 = 1"
    ]

    params = {
        "limit": limit
    }

    # ========================================================
    # ONLY MISSING
    # ========================================================

    if only_missing:

        missing_conditions = []

        for field in fields:

            target_col = (
                _get_target_column(
                    field,
                    target_lang,
                )
            )

            missing_conditions.append(
                f"""
                (
                    {target_col} IS NULL
                    OR TRIM({target_col}) = ''
                )
                """
            )

        where_clauses.append(
            "("
            + " OR ".join(
                missing_conditions
            )
            + ")"
        )

    # ========================================================
    # CONTENT IDS
    # ========================================================

    if content_ids:

        where_clauses.append(
            """
            ID_CONTENT IN UNNEST(
                @content_ids
            )
            """
        )

        params["content_ids"] = (
            content_ids
        )

    # ========================================================
    # SOURCE
    # ========================================================

    if source_id:

        where_clauses.append(
            "SOURCE_ID = @source_id"
        )

        params["source_id"] = source_id

    # ========================================================
    # CONTENT TYPE
    # ========================================================

    if content_type:

        where_clauses.append(
            """
            UPPER(CONTENT_TYPE)
            = UPPER(@content_type)
            """
        )

        params["content_type"] = (
            content_type
        )

    # ========================================================
    # QUERY
    # ========================================================

    sql = f"""
    SELECT
        ID_CONTENT

    FROM `{TABLE_CONTENT}`

    WHERE
        {" AND ".join(where_clauses)}

    ORDER BY
        PUBLISHED_AT DESC

    LIMIT @limit
    """

    rows = query_bq(
        sql,
        params
    )

    translated_ids = []

    # ========================================================
    # LOOP
    # ========================================================

    for row in rows:

        content_id = row["ID_CONTENT"]

        try:

            translate_content_fields(
                content_id=content_id,
                target_lang=target_lang,
                fields=fields,
            )

            translated_ids.append(
                content_id
            )

        except Exception as e:

            print(
                "❌ Translation batch error:",
                content_id,
                e
            )

    return {
        "translated_count": len(
            translated_ids
        ),

        "translated_ids":
            translated_ids,
    }
