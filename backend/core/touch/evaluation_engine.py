import json
import re

from typing import (
    Optional,
)

from core.touch.evaluation_prompt import (
    TOUCH_EVALUATION_SYSTEM_PROMPT,
    build_touch_evaluation_prompt,
)

from core.touch.search_models import (
    TouchCandidateEvaluationResult,
    TouchContentCandidate,
    TouchContentDecision,
    TouchResearchBrief,
    TouchResearchInterpretation,
)

from utils.llm import (
    run_llm_json,
)


# ============================================================
# CONFIGURATION
# ============================================================

DEFAULT_TOUCH_EVALUATION_BATCH_SIZE = 6

DEFAULT_TOUCH_EVALUATION_ATTEMPTS = 2


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
            "d’évaluation Touch"
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
                "la réponse d’évaluation Touch"
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
                "moteur d’évaluation Touch"
            ) from exc

    if not isinstance(
        parsed,
        dict,
    ):

        raise ValueError(
            "La réponse d’évaluation Touch "
            "n’est pas un objet JSON"
        )

    return parsed


# ============================================================
# NORMALIZE EVENT KEY
# ============================================================

def _normalize_event_key(
    event_key: str | None,
) -> str | None:

    if not isinstance(
        event_key,
        str,
    ):

        return None

    normalized = re.sub(
        r"[^a-z0-9]+",
        "-",
        event_key.lower(),
    )

    normalized = normalized.strip(
        "-"
    )

    return (
        normalized
        if normalized
        else None
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
# BUILD CANDIDATE BATCHES
# ============================================================

def _build_candidate_batches(
    candidates: list[
        TouchContentCandidate
    ],
    batch_size: int,
) -> list[
    list[TouchContentCandidate]
]:

    batch_size = max(
        1,
        batch_size,
    )

    return [

        candidates[
            start:
            start + batch_size
        ]

        for start in range(
            0,
            len(
                candidates
            ),
            batch_size,
        )

    ]


# ============================================================
# VALIDATE DECISION IDS
# ============================================================

def _validate_decision_ids(
    candidates: list[
        TouchContentCandidate
    ],
    evaluation: (
        TouchCandidateEvaluationResult
    ),
) -> None:

    candidate_ids = [

        candidate.content_id

        for candidate in candidates

    ]

    decision_ids = [

        decision.content_id

        for decision in evaluation.decisions

    ]

    if len(
        decision_ids
    ) != len(
        set(
            decision_ids
        )
    ):

        raise ValueError(
            "Le moteur Touch a retourné des "
            "content_id en double"
        )

    candidate_id_set = set(
        candidate_ids
    )

    decision_id_set = set(
        decision_ids
    )

    unknown_ids = (
        decision_id_set
        - candidate_id_set
    )

    if unknown_ids:

        raise ValueError(
            "Le moteur Touch a inventé des "
            "content_id : "
            + ", ".join(
                sorted(
                    unknown_ids
                )
            )
        )

    missing_ids = (
        candidate_id_set
        - decision_id_set
    )

    if missing_ids:

        raise ValueError(
            "Le moteur Touch a omis des "
            "content_id : "
            + ", ".join(
                sorted(
                    missing_ids
                )
            )
        )

    if len(
        decision_ids
    ) != len(
        candidate_ids
    ):

        raise ValueError(
            "Le nombre de décisions Touch "
            "ne correspond pas au nombre "
            "de candidats"
        )


# ============================================================
# VALIDATE CROSS REFERENCES
# ============================================================

def _validate_cross_references(
    candidates: list[
        TouchContentCandidate
    ],
    evaluation: (
        TouchCandidateEvaluationResult
    ),
) -> None:

    candidate_ids = {

        candidate.content_id

        for candidate in candidates

    }

    for decision in evaluation.decisions:

        referenced_ids = (

            decision.overlaps_with

            + decision.contradictions_with

        )

        unknown_ids = {

            content_id

            for content_id in referenced_ids

            if content_id not in candidate_ids

        }

        if unknown_ids:

            raise ValueError(
                "Le moteur Touch a inventé des "
                "références croisées pour "
                f"{decision.content_id}: "
                + ", ".join(
                    sorted(
                        unknown_ids
                    )
                )
            )

        if (
            decision.content_id
            in referenced_ids
        ):

            raise ValueError(
                "Un contenu Touch ne peut pas "
                "se référencer lui-même : "
                f"{decision.content_id}"
            )


# ============================================================
# NORMALIZE DECISION
# ============================================================

def _normalize_decision(
    decision: TouchContentDecision,
) -> TouchContentDecision:

    overlaps_with = list(
        dict.fromkeys(
            decision.overlaps_with
        )
    )

    contradictions_with = list(
        dict.fromkeys(
            decision.contradictions_with
        )
    )

    return decision.model_copy(

        update={

            "event_key":
                _normalize_event_key(
                    decision.event_key
                ),

            "reason":
                decision.reason.strip(),

            "coverage_dimensions":
                list(
                    dict.fromkeys(
                        decision
                        .coverage_dimensions
                    )
                ),

            "key_contributions":
                _unique_text_values(
                    decision.key_contributions
                ),

            "overlaps_with":
                overlaps_with,

            "contradictions_with":
                contradictions_with,

        },

    )


# ============================================================
# NORMALIZE EVALUATION
# ============================================================

def _normalize_evaluation(
    evaluation: (
        TouchCandidateEvaluationResult
    ),
) -> TouchCandidateEvaluationResult:

    return TouchCandidateEvaluationResult(

        decisions=[

            _normalize_decision(
                decision
            )

            for decision in (
                evaluation.decisions
            )

        ],

    )


# ============================================================
# RELEVANCE ORDER
# ============================================================

def _relevance_order(
    relevance: str,
) -> int:

    relevance_order = {

        "DIRECT": 0,

        "CONTEXT": 1,

        "RELATED": 2,

        "OUT_OF_SCOPE": 3,

    }

    return relevance_order.get(
        relevance,
        4,
    )


# ============================================================
# SORT DECISIONS
# ============================================================

def _sort_decisions(
    decisions: list[
        TouchContentDecision
    ],
) -> list[
    TouchContentDecision
]:

    return sorted(

        decisions,

        key=lambda decision: (

            _relevance_order(
                decision.relevance
            ),

            -decision.relevance_score,

        ),

    )


# ============================================================
# BUILD RETRY PROMPT
# ============================================================

def _build_evaluation_retry_prompt(
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

Return exactly one decision for every candidate supplied in
this batch.

Do not omit any content_id.

Do not invent or modify any content_id.

Do not return the same content_id more than once.

overlaps_with and contradictions_with may contain only other
content_id values supplied in this batch.

A content must never reference itself.

Return only the corrected JSON object.
""".strip()


# ============================================================
# EVALUATE ONE BATCH
# ============================================================

def _evaluate_candidate_batch(
    brief: TouchResearchBrief,
    interpretation: (
        TouchResearchInterpretation
    ),
    candidates: list[
        TouchContentCandidate
    ],
    model: Optional[str],
    max_attempts: int,
) -> TouchCandidateEvaluationResult:

    original_prompt = (
        build_touch_evaluation_prompt(

            brief=brief,

            interpretation=(
                interpretation
            ),

            candidates=candidates,

        )
    )

    prompt = original_prompt

    last_error = (
        "Erreur inconnue du moteur "
        "d’évaluation Touch"
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
                    TOUCH_EVALUATION_SYSTEM_PROMPT
                ),

            )

            parsed = _extract_json_object(
                raw_content
            )

            evaluation = (
                TouchCandidateEvaluationResult
                .model_validate(
                    parsed
                )
            )

            evaluation = (
                _normalize_evaluation(
                    evaluation
                )
            )

            _validate_decision_ids(

                candidates=candidates,

                evaluation=evaluation,

            )

            _validate_cross_references(

                candidates=candidates,

                evaluation=evaluation,

            )

            return evaluation

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
                _build_evaluation_retry_prompt(

                    original_prompt=(
                        original_prompt
                    ),

                    error=last_error,

                )
            )

    raise ValueError(
        "Échec de l’évaluation d’un lot Touch "
        f"après {max_attempts} tentative(s) : "
        f"{last_error}"
    )


# ============================================================
# EVALUATE TOUCH CANDIDATES
# ============================================================

def evaluate_touch_candidates(
    brief: TouchResearchBrief,
    interpretation: (
        TouchResearchInterpretation
    ),
    candidates: list[
        TouchContentCandidate
    ],
    model: Optional[str] = None,
    batch_size: int = (
        DEFAULT_TOUCH_EVALUATION_BATCH_SIZE
    ),
) -> tuple[
    TouchCandidateEvaluationResult,
    list[str],
]:

    if not candidates:

        return (
            TouchCandidateEvaluationResult(
                decisions=[],
            ),
            [],
        )

    candidate_batches = (
        _build_candidate_batches(

            candidates=candidates,

            batch_size=batch_size,

        )
    )

    all_decisions: list[
        TouchContentDecision
    ] = []

    errors: list[str] = []

    for batch_index, candidate_batch in (
        enumerate(
            candidate_batches,
            start=1,
        )
    ):

        try:

            batch_evaluation = (
                _evaluate_candidate_batch(

                    brief=brief,

                    interpretation=(
                        interpretation
                    ),

                    candidates=(
                        candidate_batch
                    ),

                    model=model,

                    max_attempts=(
                        DEFAULT_TOUCH_EVALUATION_ATTEMPTS
                    ),

                )
            )

            all_decisions.extend(
                batch_evaluation.decisions
            )

        except Exception as exc:

            errors.append(

                "Échec de l’évaluation Touch "
                f"du lot {batch_index}: "
                f"{str(exc)[:1000]}"

            )

    evaluation = (
        TouchCandidateEvaluationResult(

            decisions=_sort_decisions(
                all_decisions
            ),

        )
    )

    return (
        evaluation,
        errors,
    )
