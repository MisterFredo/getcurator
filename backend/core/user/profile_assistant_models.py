from typing import (
    Literal,
    Optional,
    Self,
)

from pydantic import (
    BaseModel,
    ConfigDict,
    model_validator,
)


# ============================================================
# PROFILE ASSISTANT RESULT
# ============================================================

class ProfileAssistantResult(
    BaseModel,
):

    model_config = ConfigDict(
        extra="forbid",
    )

    action: Literal[
        "ASK",
        "PROPOSE",
    ]

    message: str

    proposed_profile_text: Optional[str] = None

    profile_complete: bool = False


    @model_validator(
        mode="after",
    )
    def validate_action_result(
        self,
    ) -> Self:

        if self.action == "ASK":

            if self.proposed_profile_text:

                raise ValueError(
                    "ASK ne doit pas contenir "
                    "de proposition de profil"
                )

            if self.profile_complete:

                raise ValueError(
                    "ASK doit avoir "
                    "profile_complete=false"
                )

        if self.action == "PROPOSE":

            if not (
                self.proposed_profile_text
                and self
                .proposed_profile_text
                .strip()
            ):

                raise ValueError(
                    "PROPOSE doit contenir "
                    "un profil complet"
                )

            if not self.profile_complete:

                raise ValueError(
                    "PROPOSE doit avoir "
                    "profile_complete=true"
                )

        return self
