import logging
import json

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

from utils.llm import run_llm

from core.translation.drawer_translation_service import (
    translate_fields,
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
        "source": "TITLE_EN",
        "target": "TITLE",
    },

    "EXCERPT": {
        "source": "EXCERPT_EN",
        "target": "EXCERPT",
    },

    "CONTENT_BODY": {
        "source": "CONTENT_BODY_EN",
        "target": "CONTENT_BODY",
    },

    "SIGNAL_ANALYTIQUE": {
        "source": "SIGNAL_ANALYTIQUE_EN",
        "target": "SIGNAL_ANALYTIQUE",
    },

    "MECANIQUE_EXPLIQUEE": {
        "source": "MECANIQUE_EXPLIQUEE_EN",
        "target": "MECANIQUE_EXPLIQUEE",
    },

    "ENJEU_STRATEGIQUE": {
        "source": "ENJEU_STRATEGIQUE_EN",
        "target": "ENJEU_STRATEGIQUE",
    },

    "POINT_DE_FRICTION": {
        "source": "POINT_DE_FRICTION_EN",
        "target": "POINT_DE_FRICTION",
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

        normalized = (
            field.upper()
        )

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

    if target_lang != "fr":

        raise ValueError(
            f"Langue non supportée : {target_lang}"
        )

    if field not in FIELD_MAPPING:

        raise ValueError(
            f"Champ non supporté : {field}"
        )

    return FIELD_MAPPING[
        field
    ]["target"]


def _get_source_column(
    field: str,
) -> str:

    field = field.upper()

    if field not in FIELD_MAPPING:

        raise ValueError(
            f"Champ non supporté : {field}"
        )

    return FIELD_MAPPING[
        field
    ]["source"]


# ============================================================
# TRANSLATE ONE CONTENT
# ============================================================

def translate_content_fields(
    content_id: str,
    target_lang: str = "fr",
    fields: Optional[List[str]] = None,
    only_missing: bool = False,
) -> Dict:

    normalized_fields = (
        _normalize_fields(
            fields
        )
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
            "content_id":
                content_id,
        },
    )

    if not rows:

        raise ValueError(
            "Content introuvable"
        )

    content = rows[0]

    # ========================================================
    # BUILD ONE TRANSLATION PAYLOAD
    # ========================================================

    translation_payload = {}

    for field in normalized_fields:

        source_col = (
            _get_source_column(
                field
            )
        )

        target_col = (
            _get_target_column(
                field,
                target_lang,
            )
        )

        source_value = (
            content.get(
                source_col
            )
            or ""
        ).strip()

        target_value = (
            content.get(
                target_col
            )
            or ""
        ).strip()

        if not source_value:
            continue

        if (
            only_missing
            and target_value
        ):
            continue

        translation_payload[
            target_col
        ] = source_value

    # ========================================================
    # NOTHING TO TRANSLATE
    # ========================================================

    if not translation_payload:

        return {

            "content_id":
                content_id,

            "target_lang":
                target_lang,

            "updated_fields":
                {},

            "updated_count":
                0,
        }

    # ========================================================
    # ONE LLM CALL
    # ========================================================

    translated_fields = (
        translate_fields(

            fields=
                translation_payload,

            target_lang=
                target_lang,

            raise_on_error=
                True,
        )
    )

    # ========================================================
    # SINGLE UPDATE
    # ========================================================

    assignments = []

    params = {
        "content_id":
            content_id,
    }

    for index, target_col in enumerate(
        translation_payload.keys()
    ):

        translated_value = (
            translated_fields.get(
                target_col
            )
            or ""
        ).strip()

        if not translated_value:

            raise ValueError(
                "Traduction absente pour "
                f"le champ {target_col}."
            )

        param_name = (
            f"translated_{index}"
        )

        assignments.append(
            f"{target_col} = @{param_name}"
        )

        params[
            param_name
        ] = translated_value

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

    updated_fields = {

        target_col:
            translated_fields[
                target_col
            ]

        for target_col
        in translation_payload.keys()
    }

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
    target_lang: str = "fr",
    fields: Optional[List[str]] = None,
    limit: int = 10000,
    only_missing: bool = True,
    content_ids: Optional[List[str]] = None,
    source_id: Optional[str] = None,
    content_type: Optional[str] = None,
) -> Dict:

    normalized_fields = (
        _normalize_fields(
            fields
        )
    )

    # ========================================================
    # FILTERS
    # ========================================================

    where_clauses = [
        "1 = 1",
    ]

    params = {
        "limit":
            limit,
    }

    # ========================================================
    # ONLY MISSING
    # ========================================================

    if only_missing:

        missing_conditions = []

        for field in normalized_fields:

            source_col = (
                _get_source_column(
                    field
                )
            )

            target_col = (
                _get_target_column(
                    field,
                    target_lang,
                )
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

        params["source_id"] = (
            source_id
        )

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
        params,
    )

    translated_ids = []
    skipped_ids = []
    errors = []

    # ========================================================
    # LOOP
    # ========================================================

    for row in rows:

        content_id = (
            row["ID_CONTENT"]
        )

        try:

            result = (
                translate_content_fields(

                    content_id=
                        content_id,

                    target_lang=
                        target_lang,

                    fields=
                        normalized_fields,

                    only_missing=
                        only_missing,
                )
            )

            if (
                result[
                    "updated_count"
                ]
                > 0
            ):

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
