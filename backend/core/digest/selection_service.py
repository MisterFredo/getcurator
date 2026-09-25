import json
import re

from typing import Optional

from api.expertise.models import (
    ExpertiseProfile,
)

from core.digest.selection_models import (
    DigestCandidateSelectionResult,
    DigestContentCandidate,
    DigestContentDecision,
    DigestSelectionOutcome,
)

from core.digest.selection_prompt import (
    DIGEST_SELECTION_SYSTEM_PROMPT,
    build_digest_selection_user_prompt,
)

from utils.llm import (
    run_llm_json,
)


# ============================================================
# CONFIGURATION
# ============================================================

DEFAULT_DIGEST_SELECTION_LIMIT = 20

DEFAULT_DIGEST_SELECTION_THRESHOLD = 60

DEFAULT_DIGEST_ADDITIONAL_LIMIT = 5

DEFAULT_DIGEST_ADDITIONAL_THRESHOLD = 40

DEFAULT_DIGEST_SELECTION_BATCH_SIZE = 15

DEFAULT_DIGEST_SELECTION_BATCH_ATTEMPTS = 2


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
            "Réponse vide du moteur de sélection"
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
                "Aucun objet JSON trouvé "
                "dans la réponse de sélection"
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
                "le moteur de sélection"
            ) from exc

    if not isinstance(
        parsed,
        dict,
    ):

        raise ValueError(
            "La réponse de sélection "
            "n'est pas un objet JSON"
        )

    return parsed


# ============================================================
# RELEVANCE CLASS ORDER
# ============================================================

def _relevance_class_order(
    relevance_class: str,
) -> int:

    relevance_classes = {
        "CORE": 0,
        "ADJACENT": 1,
        "OUT_OF_SCOPE": 2,
        "EXCLUDED": 3,
    }

    return relevance_classes.get(
        relevance_class,
        4,
    )


# ============================================================
# SORT DECISIONS
# ============================================================

def _sort_decisions(
    decisions: list[
        DigestContentDecision
    ],
) -> list[
    DigestContentDecision
]:

    return sorted(

        decisions,

        key=lambda decision: (

            _relevance_class_order(
                decision.relevance_class
            ),

            -decision.relevance_score,

        ),

    )


# ============================================================
# VALIDATE DECISION IDS
# ============================================================

def _validate_decision_ids(
    candidates: list[
        DigestContentCandidate
    ],
    selection: DigestCandidateSelectionResult,
) -> None:

    candidate_ids = [

        candidate.content_id

        for candidate in candidates

    ]

    decision_ids = [

        decision.content_id

        for decision in selection.decisions

    ]

    if len(
        decision_ids
    ) != len(
        set(
            decision_ids
        )
    ):

        raise ValueError(
            "Le moteur de sélection a retourné "
            "des content_id en double"
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
            "Le moteur de sélection a inventé "
            "un ou plusieurs content_id : "
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
            "Le moteur de sélection a omis "
            "un ou plusieurs content_id : "
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
            "Le nombre de décisions ne correspond "
            "pas au nombre de candidats"
        )


# ============================================================
# VALIDATE DECISION CONSISTENCY
# ============================================================

def _validate_decision_consistency(
    selection: DigestCandidateSelectionResult,
) -> None:

    for decision in selection.decisions:

        relevance_class = (
            decision.relevance_class
        )

        priority = decision.priority

        score = decision.relevance_score

        if relevance_class == "CORE":

            if priority != "SELECT":

                raise ValueError(
                    "Une décision CORE doit avoir "
                    "la priorité SELECT : "
                    f"{decision.content_id}"
                )

            if score < (
                DEFAULT_DIGEST_SELECTION_THRESHOLD
            ):

                raise ValueError(
                    "Une décision CORE doit avoir "
                    "un score supérieur ou égal à "
                    f"{DEFAULT_DIGEST_SELECTION_THRESHOLD} : "
                    f"{decision.content_id}"
                )

            if (
                decision
                .matched_negative_preferences
            ):

                raise ValueError(
                    "Une décision CORE ne peut pas "
                    "contenir de préférence négative : "
                    f"{decision.content_id}"
                )

            continue

        if priority != "IGNORE":

            raise ValueError(
                "Une décision non CORE doit avoir "
                "la priorité IGNORE : "
                f"{decision.content_id}"
            )

        if relevance_class == "ADJACENT":

            if not (
                DEFAULT_DIGEST_ADDITIONAL_THRESHOLD
                <= score
                < DEFAULT_DIGEST_SELECTION_THRESHOLD
            ):

                raise ValueError(
                    "Une décision ADJACENT doit avoir "
                    "un score compris entre "
                    f"{DEFAULT_DIGEST_ADDITIONAL_THRESHOLD} "
                    "et "
                    f"{DEFAULT_DIGEST_SELECTION_THRESHOLD - 1} : "
                    f"{decision.content_id}"
                )

            if (
                decision
                .matched_negative_preferences
            ):

                raise ValueError(
                    "Une décision ADJACENT ne peut pas "
                    "contenir de préférence négative : "
                    f"{decision.content_id}"
                )

            continue

        if relevance_class == "OUT_OF_SCOPE":

            if score >= (
                DEFAULT_DIGEST_ADDITIONAL_THRESHOLD
            ):

                raise ValueError(
                    "Une décision OUT_OF_SCOPE doit "
                    "avoir un score inférieur à "
                    f"{DEFAULT_DIGEST_ADDITIONAL_THRESHOLD} : "
                    f"{decision.content_id}"
                )

            continue

        if relevance_class == "EXCLUDED":

            if score > 19:

                raise ValueError(
                    "Une décision EXCLUDED doit avoir "
                    "un score inférieur ou égal à 19 : "
                    f"{decision.content_id}"
                )

            if not (
                decision
                .matched_negative_preferences
            ):

                raise ValueError(
                    "Une décision EXCLUDED doit "
                    "identifier au moins une préférence "
                    "négative : "
                    f"{decision.content_id}"
                )

            continue

        raise ValueError(
            "Classe de pertinence inconnue pour "
            f"{decision.content_id} : "
            f"{relevance_class}"
        )


# ============================================================
# BUILD CANDIDATE BATCHES
# ============================================================

def _build_candidate_batches(
    candidates: list[
        DigestContentCandidate
    ],
    batch_size: int,
) -> list[
    list[DigestContentCandidate]
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
# BUILD RETRY PROMPT
# ============================================================

def _build_batch_retry_prompt(
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

Do not invent any content_id.

Do not return the same content_id more than once.

The number of decisions must exactly match the number of
candidates.

Respect these mandatory consistency rules:

- CORE requires priority SELECT and a score from 60 to 100;
- ADJACENT requires priority IGNORE and a score from 40 to 59;
- OUT_OF_SCOPE requires priority IGNORE and a score from 0 to 39;
- EXCLUDED requires priority IGNORE and a score from 0 to 19;
- EXCLUDED must identify at least one explicit negative
  preference;
- CORE and ADJACENT must not identify a negative preference.

Return only the corrected JSON object.
""".strip()


# ============================================================
# SELECT ONE BATCH
# ============================================================

def _select_candidate_batch(
    profile: ExpertiseProfile,
    candidates: list[
        DigestContentCandidate
    ],
    selection_limit: int,
    model: Optional[str],
    max_attempts: int,
) -> DigestCandidateSelectionResult:

    original_prompt = (
        build_digest_selection_user_prompt(

            profile=profile,

            candidates=candidates,

            selection_limit=(
                min(
                    selection_limit,
                    len(
                        candidates
                    ),
                )
            ),

        )
    )

    prompt = original_prompt

    last_error = (
        "Erreur inconnue du moteur de sélection"
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
                    DIGEST_SELECTION_SYSTEM_PROMPT
                ),

            )

            parsed = _extract_json_object(
                raw_content
            )

            selection = (
                DigestCandidateSelectionResult
                .model_validate(
                    parsed
                )
            )

            _validate_decision_ids(

                candidates=candidates,

                selection=selection,

            )

            _validate_decision_consistency(
                selection
            )

            return selection

        except Exception as exc:

            last_error = str(
                exc
            )

            if (
                attempt + 1
                >= max_attempts
            ):

                break

            prompt = (
                _build_batch_retry_prompt(

                    original_prompt=(
                        original_prompt
                    ),

                    error=last_error,

                )
            )

    raise ValueError(
        "Échec de la sélection d'un lot "
        f"après {max_attempts} tentative(s) : "
        f"{last_error}"
    )


# ============================================================
# NORMALIZE EVENT KEY
# ============================================================

def _normalize_event_key(
    event_key: str | None,
) -> str:

    if not isinstance(
        event_key,
        str,
    ):

        return ""

    normalized = re.sub(
        r"[^a-z0-9]+",
        "-",
        event_key.lower(),
    )

    return normalized.strip(
        "-"
    )


# ============================================================
# DEDUPLICATE RETAINED EVENTS
# ============================================================

def _deduplicate_retained_events(
    selection: DigestCandidateSelectionResult,
    language: str,
) -> DigestCandidateSelectionResult:

    retained_event_ids: dict[
        str,
        str,
    ] = {}

    decisions = []

    for decision in selection.decisions:

        event_key = _normalize_event_key(
            decision.event_key
        )

        retained_class = (
            decision.relevance_class
            in {
                "CORE",
                "ADJACENT",
            }
        )

        if (
            not retained_class
            or not event_key
        ):

            decisions.append(
                decision
            )

            continue

        retained_content_id = (
            retained_event_ids.get(
                event_key
            )
        )

        if not retained_content_id:

            retained_event_ids[
                event_key
            ] = decision.content_id

            decisions.append(
                decision
            )

            continue

        if language == "fr":

            reason = (
                "Doublon de l’événement déjà "
                "couvert par le contenu "
                f"{retained_content_id}."
            )

        else:

            reason = (
                "Duplicate of the event already "
                "covered by content "
                f"{retained_content_id}."
            )

        decisions.append(

            decision.model_copy(

                update={

                    "priority":
                        "IGNORE",

                    "relevance_class":
                        "OUT_OF_SCOPE",

                    "relevance_score":
                        min(
                            decision.relevance_score,
                            19,
                        ),

                    "reason":
                        reason,

                    "matched_priorities":
                        [],

                    "matched_negative_preferences":
                        [],

                },

            )

        )

    return DigestCandidateSelectionResult(

        decisions=decisions,

    )


# ============================================================
# BUILD SELECTED IDS
# ============================================================

def _build_selected_content_ids(
    selection: DigestCandidateSelectionResult,
    selection_limit: int,
) -> list[str]:

    selected_ids = []

    for decision in selection.decisions:

        if decision.relevance_class != "CORE":

            continue

        if decision.priority != "SELECT":

            continue

        if (
            decision.relevance_score
            < DEFAULT_DIGEST_SELECTION_THRESHOLD
        ):

            continue

        selected_ids.append(
            decision.content_id
        )

        if (
            len(
                selected_ids
            )
            >= selection_limit
        ):

            break

    return selected_ids


# ============================================================
# BUILD ADDITIONAL IDS
# ============================================================

def _build_additional_content_ids(
    selection: DigestCandidateSelectionResult,
    selected_content_ids: list[str],
    additional_limit: int,
) -> list[str]:

    selected_id_set = set(
        selected_content_ids
    )

    additional_ids = []

    retained_event_keys: set[str] = set()

    for decision in selection.decisions:

        if (
            decision.relevance_class
            != "ADJACENT"
        ):

            continue

        if decision.priority != "IGNORE":

            continue

        if not (
            DEFAULT_DIGEST_ADDITIONAL_THRESHOLD
            <= decision.relevance_score
            < DEFAULT_DIGEST_SELECTION_THRESHOLD
        ):

            continue

        if (
            decision
            .matched_negative_preferences
        ):

            continue

        if (
            decision.content_id
            in selected_id_set
        ):

            continue

        event_key = _normalize_event_key(
            decision.event_key
        )

        if (
            event_key
            and event_key
            in retained_event_keys
        ):

            continue

        if event_key:

            retained_event_keys.add(
                event_key
            )

        additional_ids.append(
            decision.content_id
        )

        if (
            len(
                additional_ids
            )
            >= additional_limit
        ):

            break

    return additional_ids


# ============================================================
# BUILD CLASS COUNTS
# ============================================================

def _build_class_counts(
    selection: DigestCandidateSelectionResult,
) -> dict[str, int]:

    counts = {
        "CORE": 0,
        "ADJACENT": 0,
        "OUT_OF_SCOPE": 0,
        "EXCLUDED": 0,
    }

    for decision in selection.decisions:

        relevance_class = (
            decision.relevance_class
        )

        if relevance_class in counts:

            counts[
                relevance_class
            ] += 1

    return counts


# ============================================================
# LOG OUTCOME
# ============================================================

def _log_selection_outcome(
    candidate_count: int,
    selection: DigestCandidateSelectionResult,
    selected_content_ids: list[str],
    additional_content_ids: list[str],
    used_fallback: bool,
    error: str | None,
) -> None:

    class_counts = _build_class_counts(
        selection
    )

    print(
        "DIGEST_SELECTION",
        {
            "candidate_count":
                candidate_count,

            "core_count":
                class_counts[
                    "CORE"
                ],

            "adjacent_count":
                class_counts[
                    "ADJACENT"
                ],

            "out_of_scope_count":
                class_counts[
                    "OUT_OF_SCOPE"
                ],

            "excluded_count":
                class_counts[
                    "EXCLUDED"
                ],

            "selected_count":
                len(
                    selected_content_ids
                ),

            "additional_count":
                len(
                    additional_content_ids
                ),

            "used_fallback":
                used_fallback,

            "error":
                error,
        },
    )


# ============================================================
# FALLBACK
# ============================================================

def _build_fallback_outcome(
    candidates: list[
        DigestContentCandidate
    ],
    language: str,
    error: str,
) -> DigestSelectionOutcome:

    decisions = []

    for candidate in candidates:

        if language == "fr":

            reason = (
                "Contenu non classé à la suite "
                "d’une erreur du moteur de sélection."
            )

        else:

            reason = (
                "Content not classified following "
                "a selection engine error."
            )

        decisions.append(

            DigestContentDecision(

                content_id=(
                    candidate.content_id
                ),

                event_key=None,

                priority="IGNORE",

                relevance_class=(
                    "OUT_OF_SCOPE"
                ),

                relevance_score=0,

                reason=reason,

                matched_priorities=[],

                matched_negative_preferences=[],

            )

        )

    selection = (
        DigestCandidateSelectionResult(

            decisions=decisions,

        )
    )

    outcome = DigestSelectionOutcome(

        selection=selection,

        selected_content_ids=[],

        additional_content_ids=[],

        used_fallback=True,

        error=error[
            :2000
        ],

    )

    _log_selection_outcome(

        candidate_count=len(
            candidates
        ),

        selection=selection,

        selected_content_ids=[],

        additional_content_ids=[],

        used_fallback=True,

        error=outcome.error,

    )

    return outcome


# ============================================================
# SELECT DIGEST CANDIDATES
# ============================================================

def select_digest_candidates(
    profile: ExpertiseProfile,
    candidates: list[
        DigestContentCandidate
    ],
    selection_limit: int = (
        DEFAULT_DIGEST_SELECTION_LIMIT
    ),
    model: Optional[str] = None,
) -> DigestSelectionOutcome:

    selection_limit = max(
        1,
        selection_limit,
    )

    if not candidates:

        selection = (
            DigestCandidateSelectionResult(
                decisions=[],
            )
        )

        outcome = DigestSelectionOutcome(

            selection=selection,

            selected_content_ids=[],

            additional_content_ids=[],

            used_fallback=False,

            error=None,

        )

        _log_selection_outcome(

            candidate_count=0,

            selection=selection,

            selected_content_ids=[],

            additional_content_ids=[],

            used_fallback=False,

            error=None,

        )

        return outcome

    try:

        candidate_batches = (
            _build_candidate_batches(

                candidates=candidates,

                batch_size=(
                    DEFAULT_DIGEST_SELECTION_BATCH_SIZE
                ),

            )
        )

        all_decisions: list[
            DigestContentDecision
        ] = []

        for candidate_batch in (
            candidate_batches
        ):

            batch_selection = (
                _select_candidate_batch(

                    profile=profile,

                    candidates=(
                        candidate_batch
                    ),

                    selection_limit=(
                        selection_limit
                    ),

                    model=model,

                    max_attempts=(
                        DEFAULT_DIGEST_SELECTION_BATCH_ATTEMPTS
                    ),

                )
            )

            all_decisions.extend(
                batch_selection.decisions
            )

        selection = (
            DigestCandidateSelectionResult(

                decisions=all_decisions,

            )
        )

        # Validate the merged result against all
        # original candidates.
        _validate_decision_ids(

            candidates=candidates,

            selection=selection,

        )

        _validate_decision_consistency(
            selection
        )

        selection = (
            DigestCandidateSelectionResult(

                decisions=_sort_decisions(
                    selection.decisions
                ),

            )
        )

        selection = (
            _deduplicate_retained_events(

                selection=selection,

                language=profile.language,

            )
        )

        selection = (
            DigestCandidateSelectionResult(

                decisions=_sort_decisions(
                    selection.decisions
                ),

            )
        )

        _validate_decision_consistency(
            selection
        )

        selected_content_ids = (
            _build_selected_content_ids(

                selection=selection,

                selection_limit=(
                    selection_limit
                ),

            )
        )

        additional_content_ids = (
            _build_additional_content_ids(

                selection=selection,

                selected_content_ids=(
                    selected_content_ids
                ),

                additional_limit=(
                    DEFAULT_DIGEST_ADDITIONAL_LIMIT
                ),

            )
        )

        outcome = DigestSelectionOutcome(

            selection=selection,

            selected_content_ids=(
                selected_content_ids
            ),

            additional_content_ids=(
                additional_content_ids
            ),

            used_fallback=False,

            error=None,

        )

        _log_selection_outcome(

            candidate_count=len(
                candidates
            ),

            selection=selection,

            selected_content_ids=(
                selected_content_ids
            ),

            additional_content_ids=(
                additional_content_ids
            ),

            used_fallback=False,

            error=None,

        )

        return outcome

    except Exception as exc:

        return _build_fallback_outcome(

            candidates=candidates,

            language=profile.language,

            error=str(
                exc
            ),

        )
