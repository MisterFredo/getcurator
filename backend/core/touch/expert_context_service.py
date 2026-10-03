from typing import (
    TypeVar,
)

from pydantic import ValidationError

from core.touch.expert_context_models import (
    TouchExpertContext,
)

from core.touch.search_models import (
    TouchResearchBrief,
    TouchEntityReference,
)

from core.touch.guided_research_models import (
    TouchGuidedResearchRequest,
)

from core.user.profile_models import (
    StructuredUserProfile,
)

from core.user.user_service import (
    get_user_by_id,
)

from core.user.user_profile_service import (
    get_user_profile,
)


# ============================================================
# TYPES
# ============================================================

TouchExpertRequest = TypeVar(
    "TouchExpertRequest",
    TouchResearchBrief,
    TouchGuidedResearchRequest,
)


# ============================================================
# LOAD EXPERT CONTEXT
# ============================================================

def load_touch_expert_context(
    expert_id: str | None,
) -> TouchExpertContext | None:
    """Read an existing expert profile without regenerating it."""

    if expert_id is None:
        return None

    cleaned_id = expert_id.strip()

    if not cleaned_id:
        raise ValueError(
            "L’identifiant de l’expert Touch est vide."
        )

    account = get_user_by_id(
        cleaned_id
    )

    if not account:
        raise ValueError(
            "Expert Touch introuvable."
        )

    if account.get("PROFILE_TYPE") != "EXPERT":
        raise ValueError(
            "Le profil sélectionné n’est pas un expert."
        )

    profile = get_user_profile(
        user_id=cleaned_id,
    ) or {}

    if profile.get("profile_structured_status") != "READY":
        raise ValueError(
            "Le profil structuré de l’expert doit être "
            "prêt et à jour avant son utilisation dans Touch."
        )

    stored_profile = profile.get(
        "structured_profile"
    )

    if not stored_profile:
        raise ValueError(
            "L’expert ne possède pas de profil structuré."
        )

    try:
        structured_profile = StructuredUserProfile.model_validate(
            stored_profile
        )
    except ValidationError as exc:
        raise ValueError(
            "Le profil structuré de l’expert est invalide."
        ) from exc

    if not structured_profile.watch_instructions:
        raise ValueError(
            "Le profil de l’expert ne contient aucun axe de veille."
        )

    display_name = (
        account.get("DISPLAY_NAME")
        or account.get("NAME")
        or cleaned_id
    )

    return TouchExpertContext(
        expert_id=cleaned_id,
        display_name=display_name,
        structured_profile=structured_profile,
        source_hash=profile.get("profile_source_hash"),
        transformer_version=profile.get(
            "profile_transformer_version"
        ),
    )


# ============================================================
# ATTACH SERVER CONTEXT
# ============================================================

def prepare_touch_expert_request(
    request: TouchExpertRequest,
) -> TouchExpertRequest:
    """Return a copy with a freshly loaded authoritative context."""

    context = load_touch_expert_context(
        expert_id=request.expert_id,
    )

    prepared_request = request.model_copy()

    prepared_request._expert_context = context

    if context is not None:
        prepared_request.expert_id = context.expert_id

    return prepared_request


# ============================================================
# BUILD PROMPT PAYLOAD
# ============================================================

def build_touch_expert_context_payload(
    request: TouchResearchBrief | TouchGuidedResearchRequest,
) -> dict | None:
    """Expose context deliberately to an internal LLM prompt only."""

    if request.expert_id and request._expert_context is None:
        raise ValueError(
            "Le contexte expert Touch n’a pas été chargé."
        )

    if request._expert_context is None:
        return None

    return request._expert_context.model_dump(
        mode="json",
    )


# ============================================================
# EXPERT ENTITY REFERENCES
# ============================================================

def get_touch_expert_entities(
    request: TouchResearchBrief | TouchGuidedResearchRequest,
) -> list[TouchEntityReference]:
    """Available anchors; the research plan selects the relevant ones."""

    context = request._expert_context

    if context is None:
        return []

    references = []

    for instruction in context.structured_profile.watch_instructions:
        references.extend(instruction.entities)

    for lens in context.structured_profile.decision_lenses:
        references.extend(lens.related_entities)

    entities = []
    seen = set()

    for reference in references:
        if (
            reference.resolution_status != "RESOLVED"
            or not reference.entity_id
            or reference.entity_type not in {"company", "solution", "topic"}
        ):
            continue

        key = (reference.entity_type, reference.entity_id)

        if key in seen:
            continue

        seen.add(key)

        entities.append(
            TouchEntityReference(
                entity_type=reference.entity_type,
                entity_id=reference.entity_id,
                entity_label=(reference.canonical_label or reference.label),
            )
        )

    return entities
