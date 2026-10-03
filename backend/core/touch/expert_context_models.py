from pydantic import (
    BaseModel,
    ConfigDict,
)

from core.user.profile_models import (
    StructuredUserProfile,
)


# ============================================================
# SERVER-LOADED EXPERT CONTEXT
# ============================================================

class TouchExpertContext(BaseModel):
    """Expert mandate, distinct from the report definition."""

    model_config = ConfigDict(
        extra="forbid",
    )

    expert_id: str

    display_name: str

    structured_profile: StructuredUserProfile

    source_hash: str | None = None

    transformer_version: str | None = None
