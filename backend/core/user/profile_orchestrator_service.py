from typing import (
    Any,
    Dict,
    Optional,
    List,
    Tuple,
)

from core.user.user_service import get_user_by_id
from core.user.user_preferences_service import get_user_preferences_detailed

from core.user.profile_editorial_service import (
    build_profile_editorial_source_hash,
    generate_and_save_profile_editorial,
)

from core.user.profile_transformer_service import (
    build_profile_source_hash,
    transform_user_profile,
)

from core.user.user_profile_service import (
    get_user_profile,
    save_editorial_user_profile,
    mark_profile_structured_building,
    record_profile_transformation_error,
    save_validated_user_profile,
)


def _extract_preference_labels(items: Optional[List[Dict[str, Any]]]) -> List[str]:
    labels: List[str] = []
    seen = set()
    for item in items or []:
        if not isinstance(item, dict):
            continue
        label = item.get("label")
        if not isinstance(label, str) or not label.strip():
            continue
        cleaned = label.strip()
        key = cleaned.casefold()
        if key not in seen:
            seen.add(key)
            labels.append(cleaned)
    return labels


# ============================================================
# TYPES
# ============================================================

OrchestratorResult = Tuple[
    Optional[Dict[str, Any]],
    Optional[str],
]


# ============================================================
# GET CURRENT READY EDITORIAL PROFILE
# ============================================================

def get_current_ready_editorial_profile(
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
            "profile_editorial_source_hash"
        )
        != source_hash
    ):

        return None

    if (
        current_profile.get(
            "profile_editorial_status"
        )
        != "READY"
    ):

        return None

    editorial_text = (
        current_profile.get(
            "profile_editorial_text"
        )
    )

    if not (
        isinstance(
            editorial_text,
            str,
        )
        and editorial_text.strip()
    ):

        return None

    return current_profile


# ============================================================
# GET CURRENT READY STRUCTURED PROFILE
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
# CLEAN PROFILE TEXT
# ============================================================

def _clean_profile_text(
    profile_text: Optional[str],
) -> str:

    if not isinstance(
        profile_text,
        str,
    ):

        return ""

    return profile_text.strip()


# ============================================================
# BUILD EDITORIAL PROFILE
# ============================================================

def _get_or_generate_editorial_profile(
    user_id: str,
    profile_text: str,
    geography_1: Optional[str],
    geography_2: Optional[str],
    geography_3: Optional[str],
    language: str,
    force: bool,
    companies: Optional[List[str]] = None,
    solutions: Optional[List[str]] = None,
    topics: Optional[List[str]] = None,
    account_context: Optional[Dict[str, Any]] = None,
) -> Tuple[
    Optional[str],
    Optional[str],
    bool,
]:
    """
    Return:

    - editorial profile text;
    - error;
    - whether a new editorial profile was generated.
    """

    # A manually validated mandate is authoritative, including when
    # rebuilding JSON with force=True. AI proposals use a separate route.
    current = get_user_profile(user_id=user_id) or {}
    if current.get("profile_editorial_transformer_version") == "MANUAL":
        manual_text = (current.get("profile_editorial_text") or "").strip()
        if manual_text:
            return manual_text, None, False

    editorial_source_hash = (
        build_profile_editorial_source_hash(
            profile_text=profile_text,
            geography_1=geography_1,
            geography_2=geography_2,
            geography_3=geography_3,
            language=language,
            companies=companies,
            solutions=solutions,
            topics=topics,
            account_context=account_context,
        )
    )

    # ========================================================
    # REUSE CURRENT EDITORIAL PROFILE
    # ========================================================

    if not force:

        current_profile = (
            get_current_ready_editorial_profile(
                user_id=user_id,
                source_hash=(
                    editorial_source_hash
                ),
            )
        )

        if current_profile:

            editorial_text = (
                current_profile.get(
                    "profile_editorial_text"
                )
                or ""
            ).strip()

            return (
                editorial_text,
                None,
                False,
            )

    # ========================================================
    # GENERATE EDITORIAL PROFILE
    # ========================================================

    try:

        editorial_result = (
            generate_and_save_profile_editorial(
                user_id=user_id,
                profile_text=profile_text,
                geography_1=geography_1,
                geography_2=geography_2,
                geography_3=geography_3,
                language=language,
                companies=companies,
                solutions=solutions,
                topics=topics,
                account_context=account_context,
            )
        )

    except Exception as exc:

        return (
            None,
            (
                "Impossible de générer "
                f"le profil éditorial : {exc}"
            ),
            False,
        )

    editorial_text = (
        editorial_result.get(
            "editorial_text"
        )
        or ""
    ).strip()

    if not editorial_text:

        return (
            None,
            (
                "Le profil éditorial généré "
                "est vide"
            ),
            False,
        )

    return (
        editorial_text,
        None,
        True,
    )


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
        _clean_profile_text(
            profile_text
        )
    )

    if not cleaned_profile_text:

        return (
            None,
            "Impossible de structurer un profil vide",
        )

    # Resolve the target account once and reuse exactly the same inputs
    # for editorial cache lookup, generation and returned hash.
    try:
        user = get_user_by_id(user_id)
        if not user:
            return None, "Utilisateur introuvable"
        preferences = get_user_preferences_detailed(user_id=user_id) or {}
        companies = _extract_preference_labels(preferences.get("companies"))
        solutions = _extract_preference_labels(preferences.get("solutions"))
        topics = _extract_preference_labels(preferences.get("topics"))
        account_context = {
            "name": user.get("NAME"),
            "display_name": user.get("DISPLAY_NAME"),
            "company": user.get("COMPANY"),
            "description": user.get("DESCRIPTION"),
            "profile_type": user.get("PROFILE_TYPE") or "USER",
            "role": user.get("ROLE"),
        }
    except Exception as exc:
        return None, f"Impossible de récupérer le contexte du profil : {exc}"

    # ========================================================
    # EDITORIAL PROFILE
    # ========================================================

    (
        editorial_profile_text,
        editorial_error,
        editorial_generated,
    ) = _get_or_generate_editorial_profile(
        user_id=user_id,
        profile_text=cleaned_profile_text,
        geography_1=geography_1,
        geography_2=geography_2,
        geography_3=geography_3,
        language=language,
        force=force,
        companies=companies,
        solutions=solutions,
        topics=topics,
        account_context=account_context,
    )

    if (
        editorial_error
        or not editorial_profile_text
    ):

        return (
            None,
            (
                editorial_error
                or (
                    "La génération du profil "
                    "éditorial a échoué"
                )
            ),
        )

    # ========================================================
    # STRUCTURED SOURCE HASH
    # ========================================================

    structured_source_hash = (
        build_profile_source_hash(
            profile_text=cleaned_profile_text,
            geography_1=geography_1,
            geography_2=geography_2,
            geography_3=geography_3,
            language=language,
            editorial_profile_text=(
                editorial_profile_text
            ),
        )
    )

    # ========================================================
    # STRUCTURED IDEMPOTENCY
    # ========================================================

    if not force:

        current_profile = (
            get_current_ready_profile(
                user_id=user_id,
                source_hash=(
                    structured_source_hash
                ),
            )
        )

        if current_profile:

            return (
                {
                    "status":
                        "unchanged",

                    "profile_text":
                        current_profile.get(
                            "profile_text"
                        ),

                    "editorial_profile_text":
                        current_profile.get(
                            "profile_editorial_text"
                        ),

                    "editorial_generated":
                        editorial_generated,

                    "structured_profile":
                        current_profile.get(
                            "structured_profile"
                        ),

                    "editorial_source_hash":
                        current_profile.get(
                            "profile_editorial_source_hash"
                        ),

                    "source_hash":
                        structured_source_hash,

                    "warnings":
                        [],
                },
                None,
            )

    # ========================================================
    # STRUCTURED TRANSFORMATION
    # ========================================================

    mark_profile_structured_building(
        user_id=user_id,
    )

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
        editorial_profile_text=(
            editorial_profile_text
        ),
    )

    if (
        transformation_error
        or not transformer_result
    ):

        error = (
            transformation_error
            or (
                "La transformation du profil "
                "a échoué"
            )
        )

        record_profile_transformation_error(
            user_id=user_id,
            error=error,
        )

        return (
            None,
            error,
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

        error = (
            "Impossible d'enregistrer "
            f"le profil structuré : {exc}"
        )

        record_profile_transformation_error(
            user_id=user_id,
            error=error,
        )

        return (
            None,
            error,
        )

    return (
        {
            "status":
                "generated",

            "profile_text":
                cleaned_profile_text,

            "editorial_profile_text":
                editorial_profile_text,

            "editorial_generated":
                editorial_generated,

            "structured_profile":
                (
                    transformer_result
                    .structured_profile
                    .model_dump()
                ),

            "editorial_source_hash":
                (
                    build_profile_editorial_source_hash(
                        profile_text=(
                            cleaned_profile_text
                        ),
                        geography_1=geography_1,
                        geography_2=geography_2,
                        geography_3=geography_3,
                        language=language,
                        companies=companies,
                        solutions=solutions,
                        topics=topics,
                        account_context=account_context,
                    )
                ),

            "source_hash":
                (
                    transformer_result
                    .source_hash
                ),

            "schema_version":
                (
                    transformer_result
                    .schema_version
                ),

            "transformer_version":
                (
                    transformer_result
                    .transformer_version
                ),

            "warnings":
                (
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

# ============================================================
# SAVE ADMIN EDITORIAL PROFILE AND REBUILD JSON
# ============================================================

def save_and_structure_editorial_profile(
    user_id: str,
    editorial_profile_text: str,
    language: str = "fr",
    model: Optional[str] = None,
) -> OrchestratorResult:

    text = _clean_profile_text(editorial_profile_text)
    if not user_id or not text:
        return None, "Le profil éditorial ne peut pas être vide"

    current = get_user_profile(user_id=user_id)
    if not current:
        return None, "Profil utilisateur introuvable"

    # The existing version column also distinguishes a manually validated
    # mandate. No database schema change is needed.
    import hashlib
    save_editorial_user_profile(
        user_id=user_id,
        editorial_text=text,
        source_hash=hashlib.sha256(text.encode("utf-8")).hexdigest(),
        transformer_version="MANUAL",
    )
    mark_profile_structured_building(user_id=user_id)

    try:
        result, error = transform_user_profile(
            profile_text=current.get("profile_text") or "",
            editorial_profile_text=text,
            geography_1=current.get("geography_1"),
            geography_2=current.get("geography_2"),
            geography_3=current.get("geography_3"),
            language=language,
            model=model,
        )
        if error or not result:
            raise ValueError(error or "La transformation du profil a échoué")

        save_validated_user_profile(
            user_id=user_id,
            geography_1=current.get("geography_1"),
            geography_2=current.get("geography_2"),
            geography_3=current.get("geography_3"),
            profile_text=current.get("profile_text") or "",
            transformer_result=result,
        )
    except Exception as exc:
        record_profile_transformation_error(user_id=user_id, error=str(exc))
        return {
            "status": "editorial_saved_structured_error",
            "structured_error": str(exc),
        }, None

    return {"status": "saved", "warnings": result.warnings}, None
