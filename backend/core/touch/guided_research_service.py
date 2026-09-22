import json

from typing import (
    Optional,
)

from core.touch.guided_research_models import (
    TouchGuidedEntityMention,
    TouchGuidedResearchAxis,
    TouchGuidedResearchOutcome,
    TouchGuidedResearchPlan,
    TouchGuidedResearchRequest,
)

from core.touch.guided_research_prompt import (
    TOUCH_GUIDED_RESEARCH_SYSTEM_PROMPT,
    build_touch_guided_research_prompt,
)

from core.touch.search_models import (
    TouchEntityReference,
)

from utils.llm import (
    run_llm_json,
)


# ============================================================
# CONFIGURATION
# ============================================================

DEFAULT_TOUCH_GUIDED_RESEARCH_ATTEMPTS = 2

DEFAULT_TOUCH_GUIDED_MAX_QUESTIONS = 3

DEFAULT_TOUCH_GUIDED_MAX_SEARCH_TERMS = 10

DEFAULT_TOUCH_GUIDED_MAX_RELATED_ANGLES = 8


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
            "de recherche guidée Touch"
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
                "la réponse de recherche guidée Touch"
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
                "moteur de recherche guidée Touch"
            ) from exc

    if not isinstance(
        parsed,
        dict,
    ):

        raise ValueError(
            "La réponse de recherche guidée Touch "
            "n’est pas un objet JSON"
        )

    return parsed


# ============================================================
# NORMALIZE TEXT LIST
# ============================================================

def _normalize_text_list(
    values: list[str],
    maximum: int | None = None,
) -> list[str]:

    normalized_values = []

    seen_values = set()

    for value in values:

        if not isinstance(
            value,
            str,
        ):
            continue

        cleaned_value = (
            value.strip()
        )

        if not cleaned_value:
            continue

        key = (
            cleaned_value.casefold()
        )

        if key in seen_values:
            continue

        seen_values.add(
            key
        )

        normalized_values.append(
            cleaned_value
        )

        if (
            maximum is not None
            and len(
                normalized_values
            ) >= maximum
        ):
            break

    return normalized_values


# ============================================================
# SUPPLIED ENTITIES
# ============================================================

def _get_supplied_entities(
    request: TouchGuidedResearchRequest,
) -> list[
    TouchEntityReference
]:

    supplied_entities = []

    supplied_entities.extend(
        request.companies
    )

    supplied_entities.extend(
        request.solutions
    )

    supplied_entities.extend(
        request.topics
    )

    return supplied_entities


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
# VALIDATE RESOLVED ENTITIES
# ============================================================

def _validate_resolved_entities(
    request: TouchGuidedResearchRequest,
    plan: TouchGuidedResearchPlan,
) -> None:

    supplied_entities = (
        _get_supplied_entities(
            request
        )
    )

    supplied_signature = (
        _build_entity_signature(
            supplied_entities
        )
    )

    returned_signature = (
        _build_entity_signature(
            plan.resolved_entities
        )
    )

    # Les doublons indiquent toujours une réponse
    # incohérente du moteur.
    if (
        len(
            plan.resolved_entities
        )
        != len(
            returned_signature
        )
    ):

        raise ValueError(
            "Le moteur de recherche guidée "
            "a dupliqué une entité résolue"
        )

    # Le moteur ne doit jamais inventer ou modifier
    # un identifiant structuré.
    invented_entities = (
        returned_signature
        - supplied_signature
    )

    if invented_entities:

        raise ValueError(
            "Le moteur de recherche guidée "
            "a inventé ou modifié une entité résolue"
        )

    # Une entité fournie mais omise par le LLM ne provoque
    # pas d’échec. _normalize_plan réinjecte ensuite toutes
    # les entités fiables directement depuis la requête.
# ============================================================
# NORMALIZE ENTITY MENTIONS
# ============================================================

def _normalize_entity_mentions(
    mentions: list[
        TouchGuidedEntityMention
    ],
    supplied_entities: list[
        TouchEntityReference
    ],
) -> list[
    TouchGuidedEntityMention
]:

    supplied_labels = {

        (
            entity.entity_type,
            entity.entity_label.casefold(),
        )

        for entity in supplied_entities

    }

    normalized_mentions = []

    seen_mentions = set()

    for mention in mentions:

        label = (
            mention.entity_label.strip()
        )

        if not label:
            continue

        supplied_key = (
            mention.entity_type,
            label.casefold(),
        )

        # Une entité déjà fournie avec un identifiant
        # fiable ne doit pas être conservée comme mention
        # non résolue.
        if supplied_key in supplied_labels:
            continue

        mention_key = (
            mention.entity_type,
            label.casefold(),
            mention.research_role,
        )

        if mention_key in seen_mentions:
            continue

        seen_mentions.add(
            mention_key
        )

        normalized_mentions.append(

            mention.model_copy(

                update={
                    "entity_label":
                        label,
                },

            )

        )

    return normalized_mentions


# ============================================================
# VALIDATE AXES
# ============================================================

def _validate_axes(
    axes: list[
        TouchGuidedResearchAxis
    ],
) -> None:

    seen_axis_ids = set()

    for axis in axes:

        if not axis.axis_id.strip():

            raise ValueError(
                "Un axe de recherche guidée "
                "ne contient pas d’axis_id"
            )

        if axis.axis_id in seen_axis_ids:

            raise ValueError(
                "Le moteur de recherche guidée "
                "a retourné des axis_id dupliqués"
            )

        seen_axis_ids.add(
            axis.axis_id
        )

        if not axis.label.strip():

            raise ValueError(
                "Un axe de recherche guidée "
                "ne contient pas de label"
            )

        if not axis.objective.strip():

            raise ValueError(
                "Un axe de recherche guidée "
                "ne contient pas d’objectif"
            )


# ============================================================
# COLLECT SEARCH TERMS
# ============================================================

def _collect_search_terms(
    plan: TouchGuidedResearchPlan,
) -> list[str]:

    candidate_terms = []

    # Les entités structurées constituent les
    # ancres de recherche les plus fiables.
    candidate_terms.extend(

        entity.entity_label

        for entity
        in plan.resolved_entities

    )

    # Les mentions seront résolues par le frontend.
    # Leur label reste néanmoins un bon terme textuel.
    candidate_terms.extend(

        mention.entity_label

        for mention
        in plan.entity_mentions

        if mention.research_role in (
            "PRIMARY",
            "COMPARISON",
        )

    )

    candidate_terms.extend(
        plan.search_terms
    )

    for axis in plan.axes:

        candidate_terms.extend(
            axis.search_terms
        )

    return _normalize_text_list(
        candidate_terms,
        maximum=(
            DEFAULT_TOUCH_GUIDED_MAX_SEARCH_TERMS
        ),
    )


# ============================================================
# COLLECT RELATED ANGLES
# ============================================================

def _collect_related_angles(
    plan: TouchGuidedResearchPlan,
) -> list[str]:

    candidate_angles = [
        *plan.related_angles,
    ]

    for axis in plan.axes:

        candidate_angles.extend(
            axis.related_angles
        )

    return _normalize_text_list(
        candidate_angles,
        maximum=(
            DEFAULT_TOUCH_GUIDED_MAX_RELATED_ANGLES
        ),
    )


# ============================================================
# NORMALIZE PLAN
# ============================================================

def _normalize_plan(
    request: TouchGuidedResearchRequest,
    plan: TouchGuidedResearchPlan,
    ready_for_search: bool,
) -> TouchGuidedResearchPlan:

    supplied_entities = (
        _get_supplied_entities(
            request
        )
    )

    normalized_mentions = (
        _normalize_entity_mentions(

            mentions=(
                plan.entity_mentions
            ),

            supplied_entities=(
                supplied_entities
            ),

        )
    )

    normalized_plan = (
        plan.model_copy(

            update={

                # Une période explicitement fournie par
                # l’administrateur reste prioritaire.
                "period_start": (
                    request.period_start
                    if request.period_start
                    is not None
                    else plan.period_start
                ),

                "period_end": (
                    request.period_end
                    if request.period_end
                    is not None
                    else plan.period_end
                ),

                # Les identifiants fiables proviennent
                # exclusivement de la requête.
                "resolved_entities":
                    supplied_entities,

                "entity_mentions":
                    normalized_mentions,

                "ready_for_search":
                    ready_for_search,

            },

        )
    )

    normalized_plan = (
        normalized_plan.model_copy(

            update={

                "search_terms":
                    _collect_search_terms(
                        normalized_plan
                    ),

                "related_angles":
                    _collect_related_angles(
                        normalized_plan
                    ),

            },

        )
    )

    return normalized_plan


# ============================================================
# VALIDATE READY PLAN
# ============================================================

def _validate_ready_plan(
    plan: TouchGuidedResearchPlan,
) -> None:

    if not plan.subject.strip():

        raise ValueError(
            "Le plan guidé ne contient "
            "pas de sujet"
        )

    if not plan.objective.strip():

        raise ValueError(
            "Le plan guidé ne contient "
            "pas d’objectif"
        )

    if not plan.central_question.strip():

        raise ValueError(
            "Le plan guidé ne contient "
            "pas de question centrale"
        )

    if not plan.axes:

        raise ValueError(
            "Le plan guidé ne contient "
            "aucun axe de recherche"
        )

    if not plan.search_terms:

        raise ValueError(
            "Le plan guidé ne contient "
            "aucun terme de recherche"
        )

    _validate_axes(
        plan.axes
    )


# ============================================================
# NORMALIZE OUTCOME
# ============================================================

def _normalize_outcome(
    request: TouchGuidedResearchRequest,
    outcome: TouchGuidedResearchOutcome,
) -> TouchGuidedResearchOutcome:

    if outcome.plan is None:

        raise ValueError(
            "Le moteur de recherche guidée "
            "n’a retourné aucun plan"
        )

    _validate_resolved_entities(

        request=request,

        plan=outcome.plan,

    )

    phase = outcome.phase

    if (
        request.action
        == "PREPARE_PLAN"
    ):

        phase = "PLAN_READY"

    ready_for_search = (
        phase == "PLAN_READY"
    )

    normalized_plan = (
        _normalize_plan(

            request=request,

            plan=outcome.plan,

            ready_for_search=(
                ready_for_search
            ),

        )
    )

    if ready_for_search:

        _validate_ready_plan(
            normalized_plan
        )

    normalized_questions = (
        _normalize_text_list(

            outcome.questions,

            maximum=(
                DEFAULT_TOUCH_GUIDED_MAX_QUESTIONS
            ),

        )
    )

    if ready_for_search:

        normalized_questions = []

    elif not normalized_questions:

        raise ValueError(
            "Le moteur de recherche guidée "
            "n’a retourné aucune question "
            "alors que l’entretien doit continuer"
        )

    missing_information = (
        _normalize_text_list(
            [
                *outcome.missing_information,
                *normalized_plan.missing_information,
            ]
        )
    )

    return outcome.model_copy(

        update={

            "phase":
                phase,

            "assistant_message":
                outcome
                .assistant_message
                .strip(),

            "questions":
                normalized_questions,

            "plan":
                normalized_plan,

            "missing_information":
                missing_information,

            "ready_for_search":
                ready_for_search,

            "used_fallback":
                False,

            "error":
                None,

        },

    )


# ============================================================
# BUILD RETRY PROMPT
# ============================================================

def _build_guided_retry_prompt(
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

Return a provisional plan even when phase is INTERVIEW.

Return every supplied structured entity exactly as supplied in
plan.resolved_entities.

Never invent, remove, rename or modify an entity_id or an
entity_label.

When phase is INTERVIEW, return between one and three useful
questions and set ready_for_search to false.

When phase is PLAN_READY, return no questions, return at least
one research axis, return usable search terms and set
ready_for_search to true.

Do not include Markdown fences.

Do not include text outside the JSON object.
""".strip()


# ============================================================
# BUILD FALLBACK PLAN
# ============================================================

def _build_fallback_plan(
    request: TouchGuidedResearchRequest,
) -> TouchGuidedResearchPlan:

    if request.current_plan is not None:

        return request.current_plan.model_copy(

            update={

                "resolved_entities":
                    _get_supplied_entities(
                        request
                    ),

                "period_start": (
                    request.period_start
                    if request.period_start
                    is not None
                    else (
                        request
                        .current_plan
                        .period_start
                    )
                ),

                "period_end": (
                    request.period_end
                    if request.period_end
                    is not None
                    else (
                        request
                        .current_plan
                        .period_end
                    )
                ),

                "ready_for_search":
                    False,

            },

        )

    message = (
        request.message.strip()
    )

    return TouchGuidedResearchPlan(

        subject=message,

        objective=message,

        central_question=message,

        research_type="OTHER",

        scope_summary=message,

        period_start=(
            request.period_start
        ),

        period_end=(
            request.period_end
        ),

        resolved_entities=(
            _get_supplied_entities(
                request
            )
        ),

        missing_information=[

            (
                "Le cadrage doit être précisé "
                "avant de lancer la recherche."
            )
            if request.output_language == "fr"
            else (
                "The scope must be clarified "
                "before starting the research."
            )

        ],

        ready_for_search=False,

    )


# ============================================================
# BUILD FALLBACK OUTCOME
# ============================================================

def _build_fallback_outcome(
    request: TouchGuidedResearchRequest,
    error: str,
) -> TouchGuidedResearchOutcome:

    plan = _build_fallback_plan(
        request
    )

    if request.output_language == "fr":

        assistant_message = (
            "Le cadrage guidé n’a pas pu être "
            "mis à jour automatiquement. "
            "Vous pouvez reformuler votre demande "
            "ou réessayer."
        )

        questions = [
            (
                "Pouvez-vous reformuler l’objectif "
                "principal de cette recherche ?"
            )
        ]

    else:

        assistant_message = (
            "The guided research scope could not "
            "be updated automatically. "
            "You can rephrase the request or retry."
        )

        questions = [
            (
                "Could you restate the main objective "
                "of this research?"
            )
        ]

    return TouchGuidedResearchOutcome(

        phase="INTERVIEW",

        assistant_message=(
            assistant_message
        ),

        questions=questions,

        plan=plan,

        missing_information=(
            plan.missing_information
        ),

        ready_for_search=False,

        used_fallback=True,

        error=error,

    )


# ============================================================
# CONTINUE GUIDED RESEARCH
# ============================================================

def continue_touch_guided_research(
    request: TouchGuidedResearchRequest,
    model: Optional[str] = None,
    max_attempts: int = (
        DEFAULT_TOUCH_GUIDED_RESEARCH_ATTEMPTS
    ),
) -> TouchGuidedResearchOutcome:

    if (
        request.action
        in (
            "START",
            "ANSWER",
            "REVISE",
        )
        and not request.message.strip()
    ):

        raise ValueError(
            "Un message est requis pour "
            "poursuivre la recherche guidée"
        )

    original_prompt = (
        build_touch_guided_research_prompt(
            request=request,
        )
    )

    prompt = original_prompt

    last_error = (
        "Erreur inconnue du moteur "
        "de recherche guidée Touch"
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
                    TOUCH_GUIDED_RESEARCH_SYSTEM_PROMPT
                ),

            )

            parsed = _extract_json_object(
                raw_content
            )

            outcome = (
                TouchGuidedResearchOutcome
                .model_validate(
                    parsed
                )
            )

            return _normalize_outcome(

                request=request,

                outcome=outcome,

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
                _build_guided_retry_prompt(

                    original_prompt=(
                        original_prompt
                    ),

                    error=last_error,

                )
            )

    return _build_fallback_outcome(

        request=request,

        error=last_error,

    )
