from dataclasses import dataclass, field
from typing import Any


# ============================================================
# KNOWLEDGE REQUEST
# ============================================================

@dataclass(slots=True)
class KnowledgeRequest:

    user_id: str

    capabilities: list[str]

    content_ids: list[str] = field(default_factory=list)

    number_ids: list[str] = field(default_factory=list)

    expert_id: str | None = None

    period: str | None = None

    metadata: dict[str, Any] = field(default_factory=dict)


# ============================================================
# KNOWLEDGE RESULT
# ============================================================

@dataclass(slots=True)
class KnowledgeResult:

    expertise: Any

    capability_results: dict[str, str] = field(
        default_factory=dict,
    )

    metadata: dict[str, Any] = field(
        default_factory=dict,
    )
