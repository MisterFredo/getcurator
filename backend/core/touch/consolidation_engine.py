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
    TouchAxisCoverage,
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
# NORMALIZE AXIS COVERAGE
# ============================================================

def _normalize_axis_coverage(
    axis_coverage: TouchAxisCoverage,
) -> TouchAxisCoverage:

    return axis_coverage.model_copy(

        update={

            "axis_id":
                axis_coverage.axis_id.strip(),

            "axis_type":
                axis_coverage.axis_type.strip(),

            "label":
                axis_coverage.label.strip(),

            "content_ids":
                list(
                    dict.fromkeys(
                        axis_coverage.content_ids
                    )
                ),

            "summary":
                axis_coverage.summary.strip(),

            "gaps":
                _unique_text_values(
                    axis_coverage.gaps
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
            "axis_coverage": [

                _normalize_axis_coverage(
                    axis_coverage
                )
            
                for axis_coverage in (
                    coverage.axis_coverage
                )
            
            ],

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
# VALIDATE AXIS COVERAGE
# ============================================================

def _validate_axis_coverage(
    interpretation: TouchResearchInterpretation,
    evaluation: (
        TouchCandidateEvaluationResult
    ),
    consolidation: TouchConsolidationResult,
) -> None:

    expected_axes = {

        axis.axis_id:
            axis

        for axis in interpretation.axes

    }

    axis_coverage_items = (
        consolidation
        .coverage_analysis
        .axis_coverage
    )

    returned_axis_ids = [

        item.axis_id

        for item in axis_coverage_items

    ]

    if len(
        returned_axis_ids
    ) != len(
        set(
            returned_axis_ids
        )
    ):

        raise ValueError(
            "La consolidation Touch a retourné "
            "plusieurs couvertures pour le même axe"
        )

    returned_axis_id_set = set(
        returned_axis_ids
    )

    expected_axis_id_set = set(
        expected_axes
    )

    unknown_axis_ids = (

        returned_axis_id_set
        - expected_axis_id_set

    )

    if unknown_axis_ids:

        raise ValueError(
            "La consolidation Touch a inventé "
            "des axis_id : "
            + ", ".join(
                sorted(
                    unknown_axis_ids
                )
            )
        )

    missing_axis_ids = (

        expected_axis_id_set
        - returned_axis_id_set

    )

    if missing_axis_ids:

        raise ValueError(
            "La consolidation Touch a omis "
            "des axes de recherche : "
            + ", ".join(
                sorted(
                    missing_axis_ids
                )
            )
        )

    decisions_by_id = {

        decision.content_id:
            decision

        for decision in evaluation.decisions

    }

    for item in axis_coverage_items:

        expected_axis = expected_axes[
            item.axis_id
        ]

        if (
            item.axis_type
            != expected_axis.axis_type
        ):

            raise ValueError(
                "La consolidation Touch a modifié "
                "le type de l’axe "
                f"{item.axis_id}"
            )

        if (
            item.label
            != expected_axis.label
        ):

            raise ValueError(
                "La consolidation Touch a modifié "
                "le label de l’axe "
                f"{item.axis_id}"
            )

        unknown_content_ids = {

            content_id

            for content_id in (
                item.content_ids
            )

            if content_id not in (
                decisions_by_id
            )

        }

        if unknown_content_ids:

            raise ValueError(
                "La couverture de l’axe "
                f"{item.axis_id} contient des "
                "content_id inconnus : "
                + ", ".join(
                    sorted(
                        unknown_content_ids
                    )
                )
            )

        out_of_scope_ids = {

            content_id

            for content_id in (
                item.content_ids
            )

            if (
                decisions_by_id[
                    content_id
                ].relevance
                == "OUT_OF_SCOPE"
            )

        }

        if out_of_scope_ids:

            raise ValueError(
                "La couverture de l’axe "
                f"{item.axis_id} contient des "
                "contenus OUT_OF_SCOPE : "
                + ", ".join(
                    sorted(
                        out_of_scope_ids
                    )
                )
            )

        if (
            item.status == "MISSING"
            and item.content_ids
        ):

            raise ValueError(
                "Un axe MISSING ne peut pas "
                "contenir de content_id : "
                f"{item.axis_id}"
            )

        if (
            item.status
            in (
                "COVERED",
                "PARTIAL",
            )
            and not item.content_ids
        ):

            raise ValueError(
                "Un axe couvert ou partiel doit "
                "contenir au moins un content_id : "
                f"{item.axis_id}"
            )


# ============================================================
# VALIDATE CONSOLIDATION
# ============================================================

def _validate_consolidation(
    interpretation: TouchResearchInterpretation,
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

    _validate_axis_coverage(
    
        interpretation=interpretation,
    
        evaluation=evaluation,
    
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
    interpretation: (
        TouchResearchInterpretation
    ),
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

    is_french = (
        brief.output_language
        .lower()
        .startswith(
            "fr"
        )
    )

    if is_french:

        summary = (
            "Les contenus évalués ont été regroupés "
            "à partir de leurs événements, mais "
            "l’analyse globale de complémentarité "
            "n’a pas pu être générée."
        )

        axis_summary = (
            "La couverture de cet axe n’a pas "
            "pu être consolidée automatiquement."
        )

    else:

        summary = (
            "The evaluated contents were grouped "
            "from their events, but the global "
            "complementarity analysis could not "
            "be generated."
        )

        axis_summary = (
            "Coverage for this axis could not "
            "be consolidated automatically."
        )

    fallback_axis_coverage = [

        TouchAxisCoverage(

            axis_id=axis.axis_id,

            axis_type=axis.axis_type,

            label=axis.label,

            status="MISSING",

            content_ids=[],

            summary=axis_summary,

            gaps=[],

        )

        for axis in interpretation.axes

    ]

    return TouchConsolidationResult(

        event_groups=(

            _build_fallback_groups(
                evaluation=evaluation,
            )

        ),

        coverage_analysis=(

            TouchCoverageAnalysis(

                summary=summary,

                axis_coverage=(
                    fallback_axis_coverage
                ),

                ready_for_notebook=(
                    not bool(
                        interpretation.axes
                    )
                ),

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

                interpretation=interpretation,
            
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
