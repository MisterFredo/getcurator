import json
import re

from typing import (
    Optional,
)

from core.touch.consolidation_prompt import (
    TOUCH_CONSOLIDATION_SYSTEM_PROMPT,
    build_touch_consolidation_prompt,
)

from core.touch.search_models import (
    TouchCandidateEvaluationResult,
    TouchConsolidationResult,
    TouchContentCandidate,
    TouchContentDecision,
    TouchCoverageAnalysis,
    TouchEventGroup,
    TouchResearchBrief,
    TouchResearchInterpretation,
)

from utils.llm import (
    run_llm_json,
)


# ============================================================
# CONFIGURATION
# ============================================================

DEFAULT_TOUCH_CONSOLIDATION_ATTEMPTS = 2


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
            "Réponse vide du moteur de "
            "consolidation Touch"
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
                "la réponse de consolidation Touch"
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
                "moteur de consolidation Touch"
            ) from exc

    if not isinstance(
        parsed,
        dict,
    ):

        raise ValueError(
            "La réponse de consolidation Touch "
            "n’est pas un objet JSON"
        )

    return parsed


# ============================================================
# NORMALIZE EVENT KEY
# ============================================================

def _normalize_event_key(
    event_key: str,
) -> str:

    normalized = re.sub(
        r"[^a-z0-9]+",
        "-",
        event_key.lower(),
    )

    return normalized.strip(
        "-"
    )


# ============================================================
# UNIQUE TEXT VALUES
# ============================================================

def _unique_text_values(
    values: list[str],
) -> list[str]:

    unique_values = []

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

        key = cleaned_value.casefold()

        if key in seen_values:

            continue

        seen_values.add(
            key
        )

        unique_values.append(
            cleaned_value
        )

    return unique_values


# ============================================================
# NORMALIZE EVENT GROUP
# ============================================================

def _normalize_event_group(
    event_group: TouchEventGroup,
) -> TouchEventGroup:

    event_key = _normalize_event_key(
        event_group.event_key
    )

    if not event_key:

        raise ValueError(
            "Un groupe Touch possède un "
            "event_key vide"
        )

    return event_group.model_copy(

        update={

            "event_key":
                event_key,

            "label":
                event_group.label.strip(),

            "content_ids":
                list(
                    dict.fromkeys(
                        event_group.content_ids
                    )
                ),

            "shared_information":
                _unique_text_values(
                    event_group.shared_information
                ),

            "complementary_contributions":
                _unique_text_values(
                    event_group
                    .complementary_contributions
                ),

            "contradictions":
                _unique_text_values(
                    event_group.contradictions
                ),

        },

    )


# ============================================================
# NORMALIZE CONSOLIDATION
# ============================================================

def _normalize_consolidation(
    consolidation: TouchConsolidationResult,
) -> TouchConsolidationResult:

    coverage = consolidation.coverage_analysis

    normalized_coverage = coverage.model_copy(

        update={

            "summary":
                coverage.summary.strip(),

            "covered_dimensions":
                list(
                    dict.fromkeys(
                        coverage.covered_dimensions
                    )
                ),

            "missing_dimensions":
                list(
                    dict.fromkeys(
                        coverage.missing_dimensions
                    )
                ),

            "strengths":
                _unique_text_values(
                    coverage.strengths
                ),

            "gaps":
                _unique_text_values(
                    coverage.gaps
                ),

            "contradictions":
                _unique_text_values(
                    coverage.contradictions
                ),

            "suggested_follow_ups":
                _unique_text_values(
                    coverage.suggested_follow_ups
                ),

        },

    )

    return TouchConsolidationResult(

        event_groups=[

            _normalize_event_group(
                event_group
            )

            for event_group in (
                consolidation.event_groups
            )

        ],

        coverage_analysis=(
            normalized_coverage
        ),

    )


# ============================================================
# VALIDATE EVENT GROUPS
# ============================================================

def _validate_event_groups(
    evaluation: (
        TouchCandidateEvaluationResult
    ),
    consolidation: TouchConsolidationResult,
) -> None:

    decisions_by_id = {

        decision.content_id:
            decision

        for decision in evaluation.decisions

    }

    known_content_ids = set(
        decisions_by_id
    )

    grouped_content_ids = set()

    event_keys = []

    for event_group in (
        consolidation.event_groups
    ):

        event_keys.append(
            event_group.event_key
        )

        if not event_group.label:

            raise ValueError(
                "Un groupe Touch ne possède "
                "pas de label"
            )

        if not event_group.content_ids:

            raise ValueError(
                "Un groupe Touch ne possède "
                "aucun content_id"
            )

        unknown_ids = (

            set(
                event_group.content_ids
            )

            - known_content_ids

        )

        if unknown_ids:

            raise ValueError(
                "La consolidation Touch a inventé "
                "des content_id : "
                + ", ".join(
                    sorted(
                        unknown_ids
                    )
                )
            )

        for content_id in (
            event_group.content_ids
        ):

            decision = decisions_by_id[
                content_id
            ]

            if (
                decision.relevance
                == "OUT_OF_SCOPE"
            ):

                raise ValueError(
                    "La consolidation Touch a "
                    "placé un contenu OUT_OF_SCOPE "
                    "dans un groupe : "
                    f"{content_id}"
                )

            if (
                content_id
                in grouped_content_ids
            ):

                raise ValueError(
                    "La consolidation Touch a "
                    "placé un contenu dans plusieurs "
                    "groupes : "
                    f"{content_id}"
                )

            grouped_content_ids.add(
                content_id
            )

    if len(
        event_keys
    ) != len(
        set(
            event_keys
        )
    ):

        raise ValueError(
            "La consolidation Touch a retourné "
            "plusieurs groupes avec le même event_key"
        )

    expected_grouped_ids = {

        decision.content_id

        for decision in evaluation.decisions

        if (
            decision.relevance
            != "OUT_OF_SCOPE"
            and decision.event_key
        )

    }

    missing_grouped_ids = (

        expected_grouped_ids
        - grouped_content_ids

    )

    if missing_grouped_ids:

        raise ValueError(
            "La consolidation Touch a omis des "
            "contenus possédant un event_key : "
            + ", ".join(
                sorted(
                    missing_grouped_ids
                )
            )
        )


# ============================================================
# VALIDATE COVERAGE
# ============================================================

def _validate_coverage(
    consolidation: TouchConsolidationResult,
) -> None:

    coverage = (
        consolidation.coverage_analysis
    )

    conflicting_dimensions = (

        set(
            coverage.covered_dimensions
        )

        & set(
            coverage.missing_dimensions
        )

    )

    if conflicting_dimensions:

        raise ValueError(
            "Certaines dimensions Touch sont à "
            "la fois couvertes et manquantes : "
            + ", ".join(
                sorted(
                    conflicting_dimensions
                )
            )
        )


# ============================================================
# VALIDATE CONSOLIDATION
# ============================================================

def _validate_consolidation(
    evaluation: (
        TouchCandidateEvaluationResult
    ),
    consolidation: TouchConsolidationResult,
) -> None:

    _validate_event_groups(

        evaluation=evaluation,

        consolidation=consolidation,

    )

    _validate_coverage(
        consolidation=consolidation,
    )


# ============================================================
# BUILD RETRY PROMPT
# ============================================================

def _build_consolidation_retry_prompt(
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

Use only supplied content_id values.

Do not include OUT_OF_SCOPE content in an event group.

A content_id may belong to no more than one event group.

Every non-OUT_OF_SCOPE content with an event_key must appear in
one event group.

Use one unique canonical event_key per group.

A dimension cannot be both covered and missing.

Return only the corrected JSON object.
""".strip()


# ============================================================
# BUILD FALLBACK GROUPS
# ============================================================

def _build_fallback_groups(
    evaluation: (
        TouchCandidateEvaluationResult
    ),
) -> list[
    TouchEventGroup
]:

    decisions_by_event: dict[
        str,
        list[TouchContentDecision]
    ] = {}

    for decision in evaluation.decisions:

        if (
            decision.relevance
            == "OUT_OF_SCOPE"
        ):

            continue

        if not decision.event_key:

            continue

        event_key = _normalize_event_key(
            decision.event_key
        )

        if not event_key:

            continue

        decisions_by_event.setdefault(
            event_key,
            [],
        ).append(
            decision
        )

    event_groups = []

    for (
        event_key,
        decisions,
    ) in decisions_by_event.items():

        contributions = []

        for decision in decisions:

            for contribution in (
                decision.key_contributions
            ):

                contributions.append(

                    (
                        f"{decision.content_id}: "
                        f"{contribution}"
                    )

                )

        event_groups.append(

            TouchEventGroup(

                event_key=event_key,

                label=event_key.replace(
                    "-",
                    " ",
                ),

                content_ids=[

                    decision.content_id

                    for decision in decisions

                ],

                shared_information=[],

                complementary_contributions=(
                    _unique_text_values(
                        contributions
                    )
                ),

                contradictions=[],

            )

        )

    return event_groups


# ============================================================
# BUILD FALLBACK CONSOLIDATION
# ============================================================

def _build_fallback_consolidation(
    brief: TouchResearchBrief,
    evaluation: (
        TouchCandidateEvaluationResult
    ),
) -> TouchConsolidationResult:

    covered_dimensions = []

    for decision in evaluation.decisions:

        if (
            decision.relevance
            == "OUT_OF_SCOPE"
        ):

            continue

        covered_dimensions.extend(
            decision.coverage_dimensions
        )

    if brief.output_language.lower().startswith(
        "fr"
    ):

        summary = (
            "Les contenus évalués ont été regroupés "
            "à partir de leurs événements, mais "
            "l’analyse globale de complémentarité "
            "n’a pas pu être générée."
        )

    else:

        summary = (
            "The evaluated contents were grouped "
            "from their events, but the global "
            "complementarity analysis could not "
            "be generated."
        )

    return TouchConsolidationResult(

        event_groups=(
            _build_fallback_groups(
                evaluation=evaluation,
            )
        ),

        coverage_analysis=(
            TouchCoverageAnalysis(

                summary=summary,

                covered_dimensions=list(
                    dict.fromkeys(
                        covered_dimensions
                    )
                ),

                missing_dimensions=[],

                strengths=[],

                gaps=[],

                contradictions=[],

                suggested_follow_ups=[],

            )
        ),

    )


# ============================================================
# CONSOLIDATE TOUCH EVALUATION
# ============================================================

def consolidate_touch_evaluation(
    brief: TouchResearchBrief,
    interpretation: (
        TouchResearchInterpretation
    ),
    candidates: list[
        TouchContentCandidate
    ],
    evaluation: (
        TouchCandidateEvaluationResult
    ),
    model: Optional[str] = None,
    max_attempts: int = (
        DEFAULT_TOUCH_CONSOLIDATION_ATTEMPTS
    ),
) -> tuple[
    TouchConsolidationResult,
    bool,
    str | None,
]:

    if not evaluation.decisions:

        return (

            TouchConsolidationResult(

                event_groups=[],

                coverage_analysis=(
                    TouchCoverageAnalysis()
                ),

            ),

            False,

            None,

        )

    original_prompt = (
        build_touch_consolidation_prompt(

            brief=brief,

            interpretation=(
                interpretation
            ),

            candidates=candidates,

            evaluation=evaluation,

        )
    )

    prompt = original_prompt

    last_error = (
        "Erreur inconnue du moteur "
        "de consolidation Touch"
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
                    TOUCH_CONSOLIDATION_SYSTEM_PROMPT
                ),

            )

            parsed = _extract_json_object(
                raw_content
            )

            consolidation = (
                TouchConsolidationResult
                .model_validate(
                    parsed
                )
            )

            consolidation = (
                _normalize_consolidation(
                    consolidation
                )
            )

            _validate_consolidation(

                evaluation=evaluation,

                consolidation=(
                    consolidation
                ),

            )

            return (
                consolidation,
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
                _build_consolidation_retry_prompt(

                    original_prompt=(
                        original_prompt
                    ),

                    error=last_error,

                )
            )

    fallback = (
        _build_fallback_consolidation(

            brief=brief,

            evaluation=evaluation,

        )
    )

    return (
        fallback,
        True,
        last_error,
    )
