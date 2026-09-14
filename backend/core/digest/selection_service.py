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
# PRIORITY ORDER
# ============================================================

def _priority_order(
    priority: str,
) -> int:

    priorities = {
        "SELECT": 0,
        "IGNORE": 1,
    }

    return priorities.get(
        priority,
        2,
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

            _priority_order(
                decision.priority
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
# DEDUPLICATE SELECTED EVENTS
# ============================================================

def _deduplicate_selected_events(
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

        if (
            decision.priority != "SELECT"
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

                    "relevance_score":
                        min(
                            decision.relevance_score,
                            24,
                        ),

                    "reason":
                        reason,

                    "matched_priorities":
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
    selection_threshold: int,
) -> list[str]:

    selected_ids = []

    for decision in selection.decisions:

        if decision.priority != "SELECT":

            continue

        if (
            decision.relevance_score
            < selection_threshold
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
# FALLBACK
# ============================================================

def _build_fallback_outcome(
    candidates: list[
        DigestContentCandidate
    ],
    selection_limit: int,
    language: str,
    error: str,
) -> DigestSelectionOutcome:

    retained_candidates = candidates[
        :selection_limit
    ]

    retained_ids = {

        candidate.content_id

        for candidate in retained_candidates

    }

    decisions = []

    for index, candidate in enumerate(
        candidates
    ):

        retained = (
            candidate.content_id
            in retained_ids
        )

        if language == "fr":

            reason = (

                "Contenu conservé selon l’ordre "
                "de présélection après une erreur "
                "du moteur de classement."

                if retained

                else

                "Contenu non conservé en raison "
                "de la limite du Digest après une "
                "erreur du moteur de classement."
            )

        else:

            reason = (

                "Content retained according to "
                "the preselection order after a "
                "ranking engine error."

                if retained

                else

                "Content not retained because of "
                "the Digest limit after a ranking "
                "engine error."
            )

        relevance_score = (

            max(
                DEFAULT_DIGEST_SELECTION_THRESHOLD,
                69 - index,
            )

            if retained

            else 0

        )

        decisions.append(

            DigestContentDecision(

                content_id=(
                    candidate.content_id
                ),

                event_key=None,

                priority=(
                    "SELECT"
                    if retained
                    else "IGNORE"
                ),

                relevance_score=(
                    relevance_score
                ),

                reason=reason,

                matched_priorities=[],

            )

        )

    selection = (
        DigestCandidateSelectionResult(

            decisions=decisions,

        )
    )

    return DigestSelectionOutcome(

        selection=selection,

        selected_content_ids=[

            candidate.content_id

            for candidate in retained_candidates

        ],

        used_fallback=True,

        error=error[
            :2000
        ],

    )


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

        return DigestSelectionOutcome(

            selection=(
                DigestCandidateSelectionResult(
                    decisions=[],
                )
            ),

            selected_content_ids=[],

            used_fallback=False,

            error=None,

        )

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

        selection = (
            DigestCandidateSelectionResult(

                decisions=_sort_decisions(
                    selection.decisions
                ),

            )
        )

        selection = (
            _deduplicate_selected_events(

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

        selected_content_ids = (
            _build_selected_content_ids(

                selection=selection,

                selection_limit=(
                    selection_limit
                ),

                selection_threshold=(
                    DEFAULT_DIGEST_SELECTION_THRESHOLD
                ),

            )
        )

        return DigestSelectionOutcome(

            selection=selection,

            selected_content_ids=(
                selected_content_ids
            ),

            used_fallback=False,

            error=None,

        )

    except Exception as exc:

        return _build_fallback_outcome(

            candidates=candidates,

            selection_limit=(
                selection_limit
            ),

            language=profile.language,

            error=str(
                exc
            ),

        )
