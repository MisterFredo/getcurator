from typing import (
    Literal,
    Optional,
)

from pydantic import (
    BaseModel,
    root_validator,
)


# ============================================================
# PROFILE ASSISTANT RESULT
# ============================================================

class ProfileAssistantResult(
    BaseModel,
):

    action: Literal[
        "ASK",
        "PROPOSE",
    ]

    message: str

    proposed_profile_text: Optional[str] = None

    profile_complete: bool = False


    @root_validator
    def validate_action_result(
        cls,
        values,
    ):

        action = values.get(
            "action"
        )

        proposed_profile_text = values.get(
            "proposed_profile_text"
        )

        profile_complete = values.get(
            "profile_complete"
        )

        if action == "ASK":

            if proposed_profile_text:

                raise ValueError(
                    "ASK ne doit pas contenir "
                    "de proposition de profil"
                )

            if profile_complete:

                raise ValueError(
                    "ASK doit avoir "
                    "profile_complete=false"
                )

        if action == "PROPOSE":

            if not (
                proposed_profile_text
                and proposed_profile_text.strip()
            ):

                raise ValueError(
                    "PROPOSE doit contenir "
                    "un profil complet"
                )

            if not profile_complete:

                raise ValueError(
                    "PROPOSE doit avoir "
                    "profile_complete=true"
                )

        return values


    class Config:

        extra = "forbid"
