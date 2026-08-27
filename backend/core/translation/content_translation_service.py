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

    "CONTENT_BODY": {
        "source": "CONTENT_BODY",
        "target": "CONTENT_BODY_EN",
    },

    "SIGNAL_ANALYTIQUE": {
        "source": "SIGNAL_ANALYTIQUE",
        "target": "SIGNAL_ANALYTIQUE_EN",
    },

    "MECANIQUE_EXPLIQUEE": {
        "source": "MECANIQUE_EXPLIQUEE",
        "target": "MECANIQUE_EXPLIQUEE_EN",
    },

    "ENJEU_STRATEGIQUE": {
        "source": "ENJEU_STRATEGIQUE",
        "target": "ENJEU_STRATEGIQUE_EN",
    },

    "POINT_DE_FRICTION": {
        "source": "POINT_DE_FRICTION",
        "target": "POINT_DE_FRICTION_EN",
    },
}


DEFAULT_FIELDS = list(
    FIELD_MAPPING.keys()
)


# ============================================================
# HELPERS
# ============================================================

def _normalize_fields(
    fields: Optional[List[str]],
) -> List[str]:

    selected_fields = (
        fields
        if fields
        else DEFAULT_FIELDS
    )

    normalized_fields = []

    for field in selected_fields:

        normalized = field.upper()

        if normalized not in FIELD_MAPPING:

            raise ValueError(
                f"Champ non supporté : {field}"
            )

        if normalized not in normalized_fields:

            normalized_fields.append(
                normalized
            )

    return normalized_fields


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
    field: str,
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
    only_missing: bool = False,
) -> Dict:

    normalized_fields = _normalize_fields(
        fields
    )

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
            "content_id": content_id,
        },
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

    for field in normalized_fields:

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

        target_value = (
            content.get(target_col)
            or ""
        ).strip()

        if not source_value:
            continue

        if (
            only_missing
            and target_value
        ):
            continue

        translated = translate_text(
            text=source_value,
            target_lang=target_lang,
            raise_on_error=True,
        )

        if not translated:
            continue

        updated_fields[target_col] = (
            translated.strip()
        )

    # ========================================================
    # SINGLE UPDATE
    # ========================================================

    if updated_fields:

        assignments = []

        params = {
            "content_id": content_id,
        }

        for index, (
            target_col,
            translated,
        ) in enumerate(
            updated_fields.items()
        ):

            param_name = (
                f"translated_{index}"
            )

            assignments.append(
                f"{target_col} = @{param_name}"
            )

            params[param_name] = translated

        query_bq(
            f"""
            UPDATE `{TABLE_CONTENT}`

            SET
                {", ".join(assignments)}

            WHERE
                ID_CONTENT = @content_id
            """,
            params,
        )

    return {

        "content_id":
            content_id,

        "target_lang":
            target_lang,

        "updated_fields":
            updated_fields,

        "updated_count":
            len(updated_fields),
    }


# ============================================================
# TRANSLATE BATCH
# ============================================================

def translate_contents_batch(
    target_lang: str = "en",
    fields: Optional[List[str]] = None,
    limit: int = 10000,
    only_missing: bool = True,
    content_ids: Optional[List[str]] = None,
    source_id: Optional[str] = None,
) -> Dict:

    normalized_fields = _normalize_fields(
        fields
    )

    # ========================================================
    # FILTERS
    # ========================================================

    where_clauses = [
        "1 = 1",
    ]

    params = {
        "limit": limit,
    }

    # ========================================================
    # ONLY MISSING
    # ========================================================

    if only_missing:

        missing_conditions = []

        for field in normalized_fields:

            source_col = _get_source_column(
                field
            )

            target_col = _get_target_column(
                field,
                target_lang,
            )

            missing_conditions.append(
                f"""
                (
                    {source_col} IS NOT NULL
                    AND TRIM({source_col}) != ''
                    AND (
                        {target_col} IS NULL
                        OR TRIM({target_col}) = ''
                    )
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
        params,
    )

    translated_ids = []
    skipped_ids = []
    errors = []

    # ========================================================
    # LOOP
    # ========================================================

    for row in rows:

        content_id = row[
            "ID_CONTENT"
        ]

        try:

            result = translate_content_fields(
                content_id=content_id,
                target_lang=target_lang,
                fields=normalized_fields,
                only_missing=only_missing,
            )

            if result["updated_count"] > 0:

                translated_ids.append(
                    content_id
                )

            else:

                skipped_ids.append(
                    content_id
                )

        except Exception as error:

            print(
                "❌ Translation batch error:",
                content_id,
                error,
            )

            errors.append({

                "content_id":
                    content_id,

                "error":
                    str(error),
            })

    return {

        "selected_count":
            len(rows),

        "translated_count":
            len(translated_ids),

        "skipped_count":
            len(skipped_ids),

        "error_count":
            len(errors),

        "translated_ids":
            translated_ids,

        "skipped_ids":
            skipped_ids,

        "errors":
            errors,
    }
