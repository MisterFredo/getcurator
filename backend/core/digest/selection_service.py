import json

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

        parsed = json.loads(
            extracted_content
        )

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
        "MUST_HAVE": 0,
        "NICE_TO_HAVE": 1,
        "IGNORE": 2,
    }

    return priorities.get(
        priority,
        3,
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

    unknown_ids = (
        set(
            decision_ids
        )
        - set(
            candidate_ids
        )
    )

    if unknown_ids:

        raise ValueError(
            "Le moteur de sélection a inventé "
            "un ou plusieurs content_id"
        )

# ============================================================
# COMPLETE MISSING DECISIONS
# ============================================================

def _complete_missing_decisions(
    candidates: list[
        DigestContentCandidate
    ],
    selection: DigestCandidateSelectionResult,
    language: str,
) -> DigestCandidateSelectionResult:

    evaluated_ids = {

        decision.content_id

        for decision in selection.decisions

    }

    completed_decisions = list(
        selection.decisions
    )

    for candidate in candidates:

        if (
            candidate.content_id
            in evaluated_ids
        ):

            continue

        if language == "fr":

            reason = (
                "Contenu non retenu par "
                "le moteur de sélection."
            )

        else:

            reason = (
                "Content not retained by "
                "the selection engine."
            )

        completed_decisions.append(

            DigestContentDecision(

                content_id=(
                    candidate.content_id
                ),

                priority="IGNORE",

                relevance_score=0,

                reason=reason,

                matched_priorities=[],

            )

        )

    return DigestCandidateSelectionResult(

        decisions=completed_decisions,

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

        if decision.priority == "IGNORE":

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
                25,
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

                priority=(
                    "NICE_TO_HAVE"
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

        prompt = (
            build_digest_selection_user_prompt(

                profile=profile,

                candidates=candidates,

                selection_limit=(
                    selection_limit
                ),

            )
        )

        raw_content = run_llm_json(

            prompt=prompt,

            model=model,

            temperature=0.1,

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

        sorted_decisions = (
            _sort_decisions(
                selection.decisions
            )
        )

        selection = (
            DigestCandidateSelectionResult(

                decisions=sorted_decisions,

            )
        )

        selected_content_ids = (
            _build_selected_content_ids(

                selection=selection,

                selection_limit=(
                    selection_limit
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
