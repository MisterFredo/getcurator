import json

from typing import (
    Optional,
)

from core.touch.search_models import (
    TouchEntityReference,
    TouchResearchBrief,
    TouchResearchInterpretation,
)

from core.touch.search_prompt import (
    TOUCH_SEARCH_INTERPRETATION_SYSTEM_PROMPT,
    build_touch_fallback_interpretation,
    build_touch_search_interpretation_prompt,
)

from utils.llm import (
    run_llm_json,
)


# ============================================================
# CONFIGURATION
# ============================================================

DEFAULT_TOUCH_INTERPRETATION_ATTEMPTS = 2


# ============================================================
# EXTRACT JSON
# ============================================================

def _extract_json_object(
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
            "d’interprétation Touch"
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
                "la réponse d’interprétation Touch"
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
                "JSON invalide retourné par le "
                "moteur d’interprétation Touch"
            ) from exc

    if not isinstance(
        parsed,
        dict,
    ):

        raise ValueError(
            "La réponse d’interprétation Touch "
            "n’est pas un objet JSON"
        )

    return parsed


# ============================================================
# NORMALIZE TEXT LIST
# ============================================================

def _normalize_text_list(
    values: list[str],
) -> list[str]:

    normalized_values = []

    seen_values = set()

    for value in values:

        if not isinstance(
            value,
            str,
        ):

            continue

        cleaned_value = value.strip()

        if not cleaned_value:

            continue

        normalized_key = (
            cleaned_value.casefold()
        )

        if normalized_key in seen_values:

            continue

        seen_values.add(
            normalized_key
        )

        normalized_values.append(
            cleaned_value
        )

    return normalized_values


# ============================================================
# ENTITY SIGNATURE
# ============================================================

def _build_entity_signature(
    entities: list[
        TouchEntityReference
    ],
) -> set[
    tuple[str, str, str]
]:

    return {

        (
            entity.entity_type,
            entity.entity_id,
            entity.entity_label,
        )

        for entity in entities

    }


# ============================================================
# VALIDATE ENTITY GROUP
# ============================================================

def _validate_entity_group(
    supplied_entities: list[
        TouchEntityReference
    ],
    returned_entities: list[
        TouchEntityReference
    ],
    entity_group: str,
) -> None:

    supplied_signature = (
        _build_entity_signature(
            supplied_entities
        )
    )

    returned_signature = (
        _build_entity_signature(
            returned_entities
        )
    )

    if (
        len(
            returned_entities
        )
        != len(
            returned_signature
        )
    ):

        raise ValueError(
            "Le moteur Touch a retourné des "
            f"entités dupliquées dans {entity_group}"
        )

    invented_entities = (
        returned_signature
        - supplied_signature
    )

    if invented_entities:

        raise ValueError(
            "Le moteur Touch a inventé ou modifié "
            f"une entité dans {entity_group}"
        )

    missing_entities = (
        supplied_signature
        - returned_signature
    )

    if missing_entities:

        raise ValueError(
            "Le moteur Touch a omis une entité "
            f"fournie dans {entity_group}"
        )


# ============================================================
# VALIDATE INTERPRETATION ENTITIES
# ============================================================

def _validate_interpretation_entities(
    brief: TouchResearchBrief,
    interpretation: (
        TouchResearchInterpretation
    ),
) -> None:

    _validate_entity_group(

        supplied_entities=brief.companies,

        returned_entities=(
            interpretation.companies
        ),

        entity_group="companies",

    )

    _validate_entity_group(

        supplied_entities=brief.solutions,

        returned_entities=(
            interpretation.solutions
        ),

        entity_group="solutions",

    )

    _validate_entity_group(

        supplied_entities=brief.topics,

        returned_entities=(
            interpretation.topics
        ),

        entity_group="topics",

    )


# ============================================================
# VALIDATE INTERPRETATION
# ============================================================

def _validate_interpretation(
    brief: TouchResearchBrief,
    interpretation: (
        TouchResearchInterpretation
    ),
) -> None:

    if not interpretation.subject.strip():

        raise ValueError(
            "Le moteur Touch n’a pas retourné "
            "de sujet de recherche"
        )

    if not interpretation.objective.strip():

        raise ValueError(
            "Le moteur Touch n’a pas retourné "
            "d’objectif de recherche"
        )

    if not interpretation.central_question.strip():

        raise ValueError(
            "Le moteur Touch n’a pas retourné "
            "de question centrale"
        )

    if not interpretation.axes:

        raise ValueError(
            "Le moteur Touch n’a retourné aucun "
            "axe de recherche"
        )

    if not interpretation.search_terms:

        raise ValueError(
            "Le moteur Touch n’a retourné aucun "
            "terme de recherche"
        )

    _validate_interpretation_entities(

        brief=brief,

        interpretation=interpretation,

    )

# ============================================================
# NORMALIZE INTERPRETATION
# ============================================================

def _normalize_interpretation(
    interpretation: (
        TouchResearchInterpretation
    ),
) -> TouchResearchInterpretation:

    normalized_axes = [

        axis.model_copy(

            update={

                "title":
                    axis.title.strip(),

                "objective":
                    axis.objective.strip(),

                "search_terms":
                    _normalize_text_list(
                        axis.search_terms
                    ),

            },

        )

        for axis in interpretation.axes

        if (
            axis.title.strip()
            or axis.objective.strip()
            or axis.search_terms
        )

    ]

    return interpretation.model_copy(

        update={

            "subject":
                interpretation.subject.strip(),

            "objective":
                interpretation.objective.strip(),

            "central_question":
                (
                    interpretation
                    .central_question
                    .strip()
                ),

            "scope_summary":
                (
                    interpretation
                    .scope_summary
                    .strip()
                ),

            "target_context":
                (
                    interpretation
                    .target_context
                    .strip()
                    or None
                )
                if interpretation.target_context
                else None,

            "geographies":
                _normalize_text_list(
                    interpretation.geographies
                ),

            "axes":
                normalized_axes,

            "assumptions":
                _normalize_text_list(
                    interpretation.assumptions
                ),

            "editorial_cautions":
                _normalize_text_list(
                    interpretation.editorial_cautions
                ),

            "missing_information":
                _normalize_text_list(
                    interpretation.missing_information
                ),

            "search_terms":
                _normalize_text_list(
                    interpretation.search_terms
                ),

            "related_angles":
                _normalize_text_list(
                    interpretation.related_angles
                ),

            "response_message":
                (
                    interpretation
                    .response_message
                    .strip()
                ),

        },

    )

# ============================================================
# VALIDATE PREPARED INTERPRETATION
# ============================================================

def validate_touch_research_interpretation(
    brief: TouchResearchBrief,
    interpretation: (
        TouchResearchInterpretation
    ),
) -> TouchResearchInterpretation:

    normalized_interpretation = (
        _normalize_interpretation(
            interpretation
        )
    )

    _validate_interpretation(

        brief=brief,

        interpretation=(
            normalized_interpretation
        ),

    )

    return normalized_interpretation


# ============================================================
# BUILD RETRY PROMPT
# ============================================================

def _build_interpretation_retry_prompt(
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

Return one valid JSON object matching the required structure.

Return every supplied structured entity exactly as supplied.

Do not invent, remove, rename or modify any entity_id or
entity_label.

Return at least one precise search term.

Do not include Markdown fences.

Do not include text outside the JSON object.
""".strip()


# ============================================================
# INTERPRET RESEARCH BRIEF
# ============================================================

def interpret_touch_research_brief(
    brief: TouchResearchBrief,
    model: Optional[str] = None,
    max_attempts: int = (
        DEFAULT_TOUCH_INTERPRETATION_ATTEMPTS
    ),
) -> tuple[
    TouchResearchInterpretation,
    bool,
    str | None,
]:

    query = brief.query.strip()

    if not query:

        error = (
            "La demande de recherche Touch "
            "ne peut pas être vide"
        )

        fallback = (
            build_touch_fallback_interpretation(

                brief=brief,

                error=error,

            )
        )

        return (
            fallback,
            True,
            error,
        )

    original_prompt = (
        build_touch_search_interpretation_prompt(
            brief=brief,
        )
    )

    prompt = original_prompt

    last_error = (
        "Erreur inconnue du moteur "
        "d’interprétation Touch"
    )

    for attempt in range(
        max(
            1,
            max_attempts,
        )
    ):

        try:

            raw_content = run_llm_json(

                prompt=prompt,

                model=model,

                temperature=0.0,

                system_prompt=(
                    TOUCH_SEARCH_INTERPRETATION_SYSTEM_PROMPT
                ),

            )

            parsed = _extract_json_object(
                raw_content
            )

            interpretation = (
                TouchResearchInterpretation
                .model_validate(
                    parsed
                )
            )
            
            interpretation = (
                validate_touch_research_interpretation(
            
                    brief=brief,
            
                    interpretation=(
                        interpretation
                    ),
            
                )
            )

            return (
                interpretation,
                False,
                None,
            )

        except Exception as exc:

            last_error = str(
                exc
            )

            if (
                attempt + 1
                >= max(
                    1,
                    max_attempts,
                )
            ):

                break

            prompt = (
                _build_interpretation_retry_prompt(

                    original_prompt=(
                        original_prompt
                    ),

                    error=last_error,

                )
            )

    fallback = (
        build_touch_fallback_interpretation(

            brief=brief,

            error=last_error,

        )
    )

    return (
        fallback,
        True,
        last_error,
    )
