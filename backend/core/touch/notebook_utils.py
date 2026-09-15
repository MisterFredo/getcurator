import json

from typing import (
    Any,
)


# ============================================================
# EXTRACT JSON OBJECT
# ============================================================

def extract_json_object(
    raw_content: str,
) -> dict:

    content = (
        raw_content.strip()
        if isinstance(
            raw_content,
            str,
        )
        else ""
    )

    if not content:

        raise ValueError(
            "Réponse vide du moteur "
            "de notebook Touch"
        )

    try:

        parsed = json.loads(
            content
        )

    except json.JSONDecodeError:

        first_brace = content.find(
            "{"
        )

        last_brace = content.rfind(
            "}"
        )

        if (
            first_brace < 0
            or last_brace < first_brace
        ):

            raise ValueError(
                "Aucun objet JSON trouvé dans "
                "la réponse du notebook Touch"
            )

        extracted_content = content[
            first_brace:
            last_brace + 1
        ]

        try:

            parsed = json.loads(
                extracted_content
            )

        except json.JSONDecodeError as exc:

            raise ValueError(
                "JSON invalide retourné par "
                "le moteur de notebook Touch"
            ) from exc

    if not isinstance(
        parsed,
        dict,
    ):

        raise ValueError(
            "La réponse du notebook Touch "
            "n’est pas un objet JSON"
        )

    return parsed


# ============================================================
# NORMALIZE LANGUAGE
# ============================================================

def normalize_language(
    language: str,
) -> str:

    normalized = (
        language.strip().lower()
        if isinstance(
            language,
            str,
        )
        else ""
    )

    if normalized.startswith(
        "en"
    ):

        return "en"

    return "fr"


# ============================================================
# UNIQUE IDS
# ============================================================

def unique_ids(
    values: list[str],
) -> list[str]:

    result = []

    seen_values = set()

    for value in values:

        if not isinstance(
            value,
            str,
        ):

            continue

        cleaned_value = value.strip()

        if (
            not cleaned_value
            or cleaned_value in seen_values
        ):

            continue

        seen_values.add(
            cleaned_value
        )

        result.append(
            cleaned_value
        )

    return result


# ============================================================
# SAFE FLOAT
# ============================================================

def safe_float(
    value: Any,
) -> float:

    if value is None:
        return 0.0

    try:

        return float(
            value
        )

    except (
        TypeError,
        ValueError,
    ):

        return 0.0


# ============================================================
# BUILD BATCHES
# ============================================================

def build_batches(
    values: list[Any],
    batch_size: int,
) -> list[list[Any]]:

    safe_batch_size = max(
        1,
        batch_size,
    )

    return [

        values[
            start:
            start + safe_batch_size
        ]

        for start in range(
            0,
            len(
                values
            ),
            safe_batch_size,
        )

    ]


# ============================================================
# BUILD RETRY PROMPT
# ============================================================

def build_retry_prompt(
    original_prompt: str,
    error: str,
) -> str:

    return f"""
{original_prompt}


============================================================
CORRECTION REQUIRED
============================================================

The previous response was invalid.

Validation error:

{error}

Correct the response while respecting the required JSON
structure.

Use only supplied source_content_ids.

Do not invent identifiers.

Return only the corrected JSON object.
""".strip()
