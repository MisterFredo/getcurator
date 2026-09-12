from typing import (
    Any,
    Dict,
    List,
    Optional,
    Tuple,
)

from core.user.profile_transformer_service import (
    build_profile_source_hash,
    transform_user_profile,
)

from core.user.user_profile_service import (
    get_user_profile,
    save_validated_user_profile,
)


# ============================================================
# TYPES
# ============================================================

OrchestratorResult = Tuple[
    Optional[Dict[str, Any]],
    Optional[str],
]


# ============================================================
# GET CURRENT READY PROFILE
# ============================================================

def get_current_ready_profile(
    user_id: str,
    source_hash: str,
) -> Optional[Dict[str, Any]]:

    current_profile = get_user_profile(
        user_id=user_id,
    )

    if not current_profile:

        return None

    if (
        current_profile.get(
            "profile_source_hash"
        )
        != source_hash
    ):

        return None

    if (
        current_profile.get(
            "profile_structured_status"
        )
        != "READY"
    ):

        return None

    structured_profile = (
        current_profile.get(
            "structured_profile"
        )
    )

    if not structured_profile:

        return None

    return current_profile


# ============================================================
# GENERATE AND SAVE PROFILE
# ============================================================

def generate_and_save_user_profile(
    user_id: str,
    profile_text: str,
    geography_1: Optional[str] = None,
    geography_2: Optional[str] = None,
    geography_3: Optional[str] = None,
    language: str = "fr",
    model: Optional[str] = None,
    force: bool = False,
) -> OrchestratorResult:

    if not user_id:

        return (
            None,
            "user_id manquant",
        )

    cleaned_profile_text = (
        profile_text.strip()
        if isinstance(
            profile_text,
            str,
        )
        else ""
    )

    source_hash = build_profile_source_hash(
        profile_text=cleaned_profile_text,
        geography_1=geography_1,
        geography_2=geography_2,
        geography_3=geography_3,
        language=language,
    )

    # ========================================================
    # IDEMPOTENCY
    # ========================================================

    if not force:

        current_profile = (
            get_current_ready_profile(
                user_id=user_id,
                source_hash=source_hash,
            )
        )

        if current_profile:

            return (
                {
                    "status": "unchanged",
                    "profile_text": (
                        current_profile.get(
                            "profile_text"
                        )
                    ),
                    "structured_profile": (
                        current_profile.get(
                            "structured_profile"
                        )
                    ),
                    "source_hash": source_hash,
                    "warnings": [],
                },
                None,
            )

    # ========================================================
    # TRANSFORMATION
    # ========================================================

    (
        transformer_result,
        transformation_error,
    ) = transform_user_profile(
        profile_text=cleaned_profile_text,
        geography_1=geography_1,
        geography_2=geography_2,
        geography_3=geography_3,
        language=language,
        model=model,
    )

    if (
        transformation_error
        or not transformer_result
    ):

        return (
            None,
            (
                transformation_error
                or (
                    "La transformation du profil "
                    "a échoué"
                )
            ),
        )

    # ========================================================
    # SAVE VALIDATED RESULT
    # ========================================================

    try:

        save_validated_user_profile(
            user_id=user_id,
            geography_1=geography_1,
            geography_2=geography_2,
            geography_3=geography_3,
            profile_text=cleaned_profile_text,
            transformer_result=(
                transformer_result
            ),
        )

    except Exception as exc:

        return (
            None,
            (
                "Impossible d'enregistrer "
                f"le profil structuré : {exc}"
            ),
        )

    return (
        {
            "status": "generated",
            "profile_text": (
                cleaned_profile_text
            ),
            "structured_profile": (
                transformer_result
                .structured_profile
                .model_dump()
            ),
            "source_hash": (
                transformer_result
                .source_hash
            ),
            "schema_version": (
                transformer_result
                .schema_version
            ),
            "transformer_version": (
                transformer_result
                .transformer_version
            ),
            "warnings": (
                transformer_result
                .warnings
            ),
        },
        None,
    )


# ============================================================
# REGENERATE CURRENT PROFILE
# ============================================================

def regenerate_current_user_profile(
    user_id: str,
    language: str = "fr",
    model: Optional[str] = None,
) -> OrchestratorResult:

    current_profile = get_user_profile(
        user_id=user_id,
    )

    if not current_profile:

        return (
            None,
            "Profil utilisateur introuvable",
        )

    return generate_and_save_user_profile(
        user_id=user_id,
        profile_text=(
            current_profile.get(
                "profile_text"
            )
            or ""
        ),
        geography_1=current_profile.get(
            "geography_1"
        ),
        geography_2=current_profile.get(
            "geography_2"
        ),
        geography_3=current_profile.get(
            "geography_3"
        ),
        language=language,
        model=model,
        force=True,
    )
