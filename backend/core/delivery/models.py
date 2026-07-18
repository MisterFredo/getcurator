from dataclasses import dataclass, field

from api.expertise.models import (
    Expertise,
)


# ============================================================
# KNOWLEDGE REQUEST
# ============================================================

@dataclass(slots=True)
class KnowledgeRequest:

    # ========================================================
    # CONTEXT
    # ========================================================

    user_id: str

    # ========================================================
    # REQUEST
    # ========================================================

    capabilities: list[str]

    content_ids: list[str] = field(
        default_factory=list,
    )

    number_ids: list[str] = field(
        default_factory=list,
    )

    expert_id: str | None = None

    period: str | None = None

    # ========================================================
    # EXTENSIONS
    # ========================================================

    metadata: dict = field(
        default_factory=dict,
    )


# ============================================================
# KNOWLEDGE RESULT
# ============================================================

@dataclass(slots=True)
class KnowledgeResult:

    # ========================================================
    # EXPERTISE
    # ========================================================

    expertise: Expertise

    # ========================================================
    # CAPABILITIES
    # ========================================================

    capability_results: dict[str, str] = field(
        default_factory=dict,
    )

    # ========================================================
    # EXTENSIONS
    # ========================================================

    metadata: dict = field(
        default_factory=dict,
    )
