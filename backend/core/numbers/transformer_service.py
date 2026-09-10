import json
import math
import re

from collections import Counter
from typing import (
    Any,
    Dict,
    List,
)

from config import (
    BQ_PROJECT,
    BQ_DATASET,
)

from utils.bigquery_utils import (
    query_bq,
)

from utils.llm import (
    run_llm,
)

from .transformer_models import (
    NumberEntityCandidate,
    NumberTransformationInput,
    NumberTransformationResult,
    TransformedNumber,
    TransformedNumberEntity,
)

from .transformer_prompt import (
    CANONICAL_SCALES,
    CANONICAL_UNITS,
    METRIC_TYPES,
    VALUE_STATUSES,
    build_number_transformer_prompt,
)


# ============================================================
# TABLES
# ============================================================

TABLE_CONTENT_ENRICHED = (
    f"{BQ_PROJECT}.{BQ_DATASET}."
    "RATECARD_CONTENT_ENRICHED"
)


# ============================================================
# HELPERS
# ============================================================

def _model_to_dict(model):

    if hasattr(model, "model_dump"):
        return model.model_dump()

    return model.dict()


def _get_value(
    row: Dict[str, Any],
    *keys: str,
):

    for key in keys:

        try:

            value = row.get(key)

        except Exception:

            value = None

        if value not in (
            None,
            "",
            "null",
        ):
            return value

    return None


def _safe_string(
    value: Any,
) -> str:

    if value is None:
        return ""

    return str(value).strip()


# ============================================================
# PARSE CHIFFRES
# ============================================================

def _parse_raw_numbers(
    value: Any,
) -> List[str]:
    """
    RATECARD_CONTENT_ENRICHED.CHIFFRES may be:

    - an ARRAY<STRING>
    - a JSON-encoded string
    - a multiline string

    This function supports all three forms.
    """

    if value is None:
        return []

    # ========================================================
    # NATIVE ARRAY
    # ========================================================

    if isinstance(value, (list, tuple)):

        return [
            _safe_string(item)
            for item in value
            if _safe_string(item)
        ]

    # ========================================================
    # STRING
    # ========================================================

    if isinstance(value, str):

        raw = value.strip()

        if not raw:
            return []

        # ----------------------------------------------------
        # JSON ARRAY
        # ----------------------------------------------------

        try:

            parsed = json.loads(raw)

            if isinstance(parsed, list):

                return [
                    _safe_string(item)
                    for item in parsed
                    if _safe_string(item)
                ]

            # Sometimes a JSON string contains
            # another JSON-encoded array.
            if isinstance(parsed, str):

                nested = json.loads(parsed)

                if isinstance(nested, list):

                    return [
                        _safe_string(item)
                        for item in nested
                        if _safe_string(item)
                    ]

        except Exception:

            pass

        # ----------------------------------------------------
        # MULTILINE FALLBACK
        # ----------------------------------------------------

        return [
            line.strip()
            for line in raw.splitlines()
            if line.strip()
        ]

    return []


# ============================================================
# ENTITY CANDIDATES
# ============================================================

def _append_candidates(
    output: List[NumberEntityCandidate],
    seen: set,
    rows: Any,
    entity_type: str,
    id_keys: tuple[str, ...],
    label_keys: tuple[str, ...],
):

    if not isinstance(rows, (list, tuple)):
        return

    for row in rows:

        if not row:
            continue

        entity_id = _get_value(
            row,
            *id_keys,
        )

        entity_label = _get_value(
            row,
            *label_keys,
        )

        if not entity_id or not entity_label:
            continue

        key = (
            entity_type,
            str(entity_id),
        )

        if key in seen:
            continue

        seen.add(key)

        output.append(
            NumberEntityCandidate(
                entity_type=entity_type,
                entity_id=str(entity_id),
                entity_label=str(entity_label),
            )
        )


def _build_entity_candidates(
    row: Dict[str, Any],
) -> List[NumberEntityCandidate]:

    candidates: List[
        NumberEntityCandidate
    ] = []

    seen = set()

    # ========================================================
    # COMPANIES
    # ========================================================

    _append_candidates(
        output=candidates,
        seen=seen,
        rows=_get_value(
            row,
            "COMPANIES",
            "companies",
        ) or [],
        entity_type="company",
        id_keys=(
            "id_company",
            "ID_COMPANY",
        ),
        label_keys=(
            "name",
            "NAME",
            "label",
            "LABEL",
        ),
    )

    # ========================================================
    # SOLUTIONS
    # ========================================================

    _append_candidates(
        output=candidates,
        seen=seen,
        rows=_get_value(
            row,
            "SOLUTIONS",
            "solutions",
        ) or [],
        entity_type="solution",
        id_keys=(
            "id_solution",
            "ID_SOLUTION",
        ),
        label_keys=(
            "name",
            "NAME",
            "label",
            "LABEL",
        ),
    )

    # ========================================================
    # TOPICS
    # ========================================================

    _append_candidates(
        output=candidates,
        seen=seen,
        rows=_get_value(
            row,
            "TOPICS",
            "topics",
        ) or [],
        entity_type="topic",
        id_keys=(
            "id_topic",
            "ID_TOPIC",
        ),
        label_keys=(
            "label",
            "LABEL",
            "name",
            "NAME",
        ),
    )

    return candidates


# ============================================================
# LOAD CONTENT
# ============================================================

def load_number_transformation_input(
    id_content: str,
) -> NumberTransformationInput:

    rows = query_bq(
        f"""
        SELECT

            ID_CONTENT,

            TITLE,

            EXCERPT,

            CONTENT_BODY,

            PUBLISHED_AT,

            CHIFFRES,

            COMPANIES,

            SOLUTIONS,

            TOPICS

        FROM `{TABLE_CONTENT_ENRICHED}`

        WHERE ID_CONTENT = @id_content

        LIMIT 1
        """,
        {
            "id_content": id_content,
        },
    ) or []

    if not rows:

        raise ValueError(
            f"Content not found: {id_content}"
        )

    row = rows[0]

    raw_numbers = _parse_raw_numbers(
        _get_value(
            row,
            "CHIFFRES",
            "chiffres",
        )
    )

    candidates = _build_entity_candidates(
        row
    )

    return NumberTransformationInput(

        id_content=str(
            _get_value(
                row,
                "ID_CONTENT",
                "id_content",
            )
        ),

        title=_safe_string(
            _get_value(
                row,
                "TITLE",
                "title",
            )
        ),

        excerpt=_safe_string(
            _get_value(
                row,
                "EXCERPT",
                "excerpt",
            )
        ),

        content_body=_safe_string(
            _get_value(
                row,
                "CONTENT_BODY",
                "content_body",
            )
        ),

        published_at=_get_value(
            row,
            "PUBLISHED_AT",
            "published_at",
        ),

        raw_numbers=raw_numbers,

        entity_candidates=candidates,

    )


# ============================================================
# SAFE JSON PARSE
# ============================================================

def _safe_parse_json(
    response: Any,
) -> Dict[str, Any]:

    if isinstance(response, dict):
        return response

    if not isinstance(response, str):
        raise ValueError(
            "Transformer response is not a string"
        )

    text = response.strip()

    if not text:
        raise ValueError(
            "Empty transformer response"
        )

    # ========================================================
    # DIRECT JSON
    # ========================================================

    try:

        parsed = json.loads(text)

        if isinstance(parsed, dict):
            return parsed

    except Exception:

        pass

    # ========================================================
    # MARKDOWN CODE FENCE
    # ========================================================

    fence_match = re.search(
        r"```(?:json)?\s*(\{.*\})\s*```",
        text,
        re.DOTALL | re.IGNORECASE,
    )

    if fence_match:

        try:

            parsed = json.loads(
                fence_match.group(1)
            )

            if isinstance(parsed, dict):
                return parsed

        except Exception:

            pass

    # ========================================================
    # JSON OBJECT FALLBACK
    # ========================================================

    object_match = re.search(
        r"\{.*\}",
        text,
        re.DOTALL,
    )

    if object_match:

        try:

            parsed = json.loads(
                object_match.group()
            )

            if isinstance(parsed, dict):
                return parsed

        except Exception:

            pass

    raise ValueError(
        "Invalid JSON returned by Numbers transformer"
    )


# ============================================================
# OUTPUT NORMALIZATION
# ============================================================

def _normalize_optional_string(
    value: Any,
):

    if value in (
        None,
        "",
        "null",
        "None",
    ):
        return None

    return str(value).strip()


def _normalize_enum(
    value: Any,
):

    normalized = _normalize_optional_string(
        value
    )

    if normalized is None:
        return None

    return normalized.upper()


def _normalize_output_item(
    item: Dict[str, Any],
) -> Dict[str, Any]:

    normalized = dict(item)

    normalized["status"] = _normalize_enum(
        normalized.get("status")
    )

    normalized["metric_type"] = _normalize_enum(
        normalized.get("metric_type")
    )

    normalized["unit"] = _normalize_enum(
        normalized.get("unit")
    )

    normalized["scale"] = _normalize_enum(
        normalized.get("scale")
    )

    normalized["value_status"] = (
        _normalize_enum(
            normalized.get("value_status")
        )
        or "UNKNOWN"
    )

    normalized["label"] = (
        _normalize_optional_string(
            normalized.get("label")
        )
    )

    normalized["zone"] = (
        _normalize_optional_string(
            normalized.get("zone")
        )
    )

    normalized["period_label"] = (
        _normalize_optional_string(
            normalized.get("period_label")
        )
    )

    normalized["reason"] = (
        _normalize_optional_string(
            normalized.get("reason")
        )
    )

    normalized["entities"] = (
        normalized.get("entities")
        or []
    )

    return normalized


# ============================================================
# VALIDATION
# ============================================================

def _validate_finite_number(
    value: Any,
    field_name: str,
):

    if value is None:
        return

    if isinstance(value, bool):

        raise ValueError(
            f"{field_name} cannot be boolean"
        )

    try:

        numeric_value = float(value)

    except Exception as exc:

        raise ValueError(
            f"Invalid {field_name}: {value}"
        ) from exc

    if not math.isfinite(numeric_value):

        raise ValueError(
            f"{field_name} must be finite"
        )


def _validate_transformed_number(
    number: TransformedNumber,
    allowed_entities: Dict[
        tuple[str, str],
        NumberEntityCandidate,
    ],
) -> TransformedNumber:

    # ========================================================
    # CANONICAL ENUMS
    # ========================================================

    if (
        number.metric_type is not None
        and number.metric_type
        not in METRIC_TYPES
    ):

        raise ValueError(
            "Invalid metric_type "
            f"for raw line '{number.raw_line}': "
            f"{number.metric_type}"
        )

    if (
        number.unit is not None
        and number.unit
        not in CANONICAL_UNITS
    ):

        raise ValueError(
            "Invalid unit "
            f"for raw line '{number.raw_line}': "
            f"{number.unit}"
        )

    if (
        number.scale is not None
        and number.scale
        not in CANONICAL_SCALES
    ):

        raise ValueError(
            "Invalid scale "
            f"for raw line '{number.raw_line}': "
            f"{number.scale}"
        )

    if (
        number.value_status
        not in VALUE_STATUSES
    ):

        raise ValueError(
            "Invalid value_status "
            f"for raw line '{number.raw_line}': "
            f"{number.value_status}"
        )

    # ========================================================
    # NUMERIC VALUES
    # ========================================================

    _validate_finite_number(
        number.value,
        "value",
    )

    _validate_finite_number(
        number.value_min,
        "value_min",
    )

    _validate_finite_number(
        number.value_max,
        "value_max",
    )

    has_single_value = (
        number.value is not None
    )

    has_complete_range = (
        number.value_min is not None
        and number.value_max is not None
    )

    has_partial_range = (
        (
            number.value_min is not None
            or number.value_max is not None
        )
        and not has_complete_range
    )

    if has_partial_range:

        raise ValueError(
            "Incomplete range for raw line: "
            f"{number.raw_line}"
        )

    if (
        has_single_value
        and has_complete_range
    ):

        raise ValueError(
            "A Number cannot contain both "
            "value and value range: "
            f"{number.raw_line}"
        )

    if (
        has_complete_range
        and number.value_min
        > number.value_max
    ):

        raise ValueError(
            "value_min is greater than "
            "value_max for raw line: "
            f"{number.raw_line}"
        )

    # ========================================================
    # ENTITY SECURITY
    # ========================================================

    validated_entities = []

    seen_entities = set()

    for entity in number.entities:

        key = (
            entity.entity_type,
            entity.entity_id,
        )

        candidate = allowed_entities.get(
            key
        )

        if candidate is None:

            raise ValueError(
                "Transformer returned an unknown "
                f"entity for raw line "
                f"'{number.raw_line}': {key}"
            )

        if key in seen_entities:
            continue

        seen_entities.add(key)

        # Always restore the official label.
        validated_entities.append(
            TransformedNumberEntity(
                entity_type=(
                    candidate.entity_type
                ),
                entity_id=(
                    candidate.entity_id
                ),
                entity_label=(
                    candidate.entity_label
                ),
            )
        )

    number.entities = validated_entities

    # ========================================================
    # STATUS RULES
    # ========================================================

    if number.status == "ACCEPTED":

        if not number.label:
            raise ValueError(
                "ACCEPTED Number without label: "
                f"{number.raw_line}"
            )

        if not number.metric_type:
            raise ValueError(
                "ACCEPTED Number without "
                "metric_type: "
                f"{number.raw_line}"
            )

        if not (
            has_single_value
            or has_complete_range
        ):
            raise ValueError(
                "ACCEPTED Number without value: "
                f"{number.raw_line}"
            )

        if not number.unit:
            raise ValueError(
                "ACCEPTED Number without unit: "
                f"{number.raw_line}"
            )

        if not number.scale:
            raise ValueError(
                "ACCEPTED Number without scale: "
                f"{number.raw_line}"
            )

        if not number.zone:
            raise ValueError(
                "ACCEPTED Number without zone: "
                f"{number.raw_line}"
            )

        if not number.period_label:
            raise ValueError(
                "ACCEPTED Number without period: "
                f"{number.raw_line}"
            )

        if not number.entities:
            raise ValueError(
                "ACCEPTED Number without entity: "
                f"{number.raw_line}"
            )

        if number.reason:
            raise ValueError(
                "ACCEPTED Number must not "
                "contain a reason: "
                f"{number.raw_line}"
            )

    elif number.status in (
        "REVIEW",
        "REJECTED",
    ):

        if not number.reason:
            raise ValueError(
                f"{number.status} Number "
                "without reason: "
                f"{number.raw_line}"
            )

    return number


def _validate_output(
    parsed: Dict[str, Any],
    data: NumberTransformationInput,
) -> List[TransformedNumber]:

    items = parsed.get("numbers")

    if not isinstance(items, list):

        raise ValueError(
            "Transformer output must contain "
            "a numbers array"
        )

    raw_input_counter = Counter(
        data.raw_numbers
    )

    raw_output_counter = Counter()

    allowed_entities = {
        (
            entity.entity_type,
            entity.entity_id,
        ): entity
        for entity in data.entity_candidates
    }

    transformed_numbers = []

    for item in items:

        if not isinstance(item, dict):

            raise ValueError(
                "Every transformed Number "
                "must be an object"
            )

        normalized_item = (
            _normalize_output_item(item)
        )

        number = TransformedNumber(
            **normalized_item
        )

        raw_output_counter[
            number.raw_line
        ] += 1

        transformed_numbers.append(
            _validate_transformed_number(
                number=number,
                allowed_entities=(
                    allowed_entities
                ),
            )
        )

    if raw_output_counter != raw_input_counter:

        missing = list(
            (
                raw_input_counter
                - raw_output_counter
            ).elements()
        )

        unexpected = list(
            (
                raw_output_counter
                - raw_input_counter
            ).elements()
        )

        raise ValueError(
            "Transformer raw-line mismatch. "
            f"Missing: {missing}. "
            f"Unexpected: {unexpected}."
        )

    return transformed_numbers


# ============================================================
# EMPTY RESULT
# ============================================================

def _build_empty_result(
    data: NumberTransformationInput,
) -> NumberTransformationResult:

    return NumberTransformationResult(

        id_content=data.id_content,

        title=data.title,

        published_at=data.published_at,

        raw_numbers_count=0,

        accepted_count=0,

        rejected_count=0,

        review_count=0,

        numbers=[],

    )


# ============================================================
# PREVIEW
# ============================================================

def preview_content_numbers(
    id_content: str,
) -> NumberTransformationResult:
    """
    Transform the Numbers of one content
    without writing anything to BigQuery.
    """

    data = load_number_transformation_input(
        id_content=id_content,
    )

    if not data.raw_numbers:

        return _build_empty_result(
            data
        )

    prompt = build_number_transformer_prompt(
        data
    )

    response = run_llm(
        prompt=prompt,
        temperature=0,
    )

    parsed = _safe_parse_json(
        response
    )

    numbers = _validate_output(
        parsed=parsed,
        data=data,
    )

    return NumberTransformationResult(

        id_content=data.id_content,

        title=data.title,

        published_at=data.published_at,

        raw_numbers_count=len(
            data.raw_numbers
        ),

        accepted_count=len([
            number
            for number in numbers
            if number.status == "ACCEPTED"
        ]),

        rejected_count=len([
            number
            for number in numbers
            if number.status == "REJECTED"
        ]),

        review_count=len([
            number
            for number in numbers
            if number.status == "REVIEW"
        ]),

        numbers=numbers,

    )


# ============================================================
# SERIALIZABLE PREVIEW
# ============================================================

def preview_content_numbers_dict(
    id_content: str,
) -> Dict[str, Any]:

    result = preview_content_numbers(
        id_content=id_content,
    )

    return _model_to_dict(
        result
    )
