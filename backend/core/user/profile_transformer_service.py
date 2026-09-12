import hashlib
import json

from typing import (
    List,
    Optional,
    Tuple,
)

from pydantic import (
    ValidationError,
)

from core.user.profile_models import (
    ProfileTransformerResult,
    StructuredUserProfile,
)

from core.user.profile_entity_resolver import (
    resolve_structured_profile_entities,
)

from core.user.profile_transformer_prompt import (
    PROFILE_SCHEMA_VERSION,
    PROFILE_TRANSFORMER_SYSTEM_PROMPT,
    PROFILE_TRANSFORMER_VERSION,
    build_profile_source_payload,
    build_profile_transformer_user_prompt,
)

from utils.llm import (
    run_llm_json,
)


# ============================================================
# TYPES
# ============================================================

TransformResult = Tuple[
    Optional[ProfileTransformerResult],
    Optional[str],
]


# ============================================================
# SOURCE HASH
# ============================================================

def build_profile_source_hash(
    profile_text: Optional[str],
    geography_1: Optional[str] = None,
    geography_2: Optional[str] = None,
    geography_3: Optional[str] = None,
    language: str = "fr",
) -> str:

    source_payload = build_profile_source_payload(
        profile_text=profile_text,
        geography_1=geography_1,
        geography_2=geography_2,
        geography_3=geography_3,
        language=language,
    )

    serialized_payload = json.dumps(
        source_payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(
            ",",
            ":",
        ),
    )

    return hashlib.sha256(
        serialized_payload.encode(
            "utf-8"
        )
    ).hexdigest()


# ============================================================
# EXTRACT JSON
# ============================================================

def extract_json_object(
    raw_content: str,
) -> dict:

    content = (
        raw_content
        .strip()
    )

    if not content:

        raise ValueError(
            "Réponse vide du moteur de transformation"
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
                "Aucun objet JSON trouvé dans la réponse"
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
                "JSON invalide retourné par le moteur"
            ) from exc

    if not isinstance(
        parsed,
        dict,
    ):

        raise ValueError(
            "Le moteur doit retourner un objet JSON"
        )

    return parsed


# ============================================================
# VALIDATE SOURCE
# ============================================================

def validate_profile_source(
    profile_text: Optional[str],
) -> Optional[str]:

    if not (
        profile_text
        and profile_text.strip()
    ):

        return (
            "Impossible de structurer "
            "un profil vide"
        )

    return None


# ============================================================
# TRANSFORM USER PROFILE
# ============================================================

def transform_user_profile(
    profile_text: Optional[str],
    geography_1: Optional[str] = None,
    geography_2: Optional[str] = None,
    geography_3: Optional[str] = None,
    language: str = "fr",
    model: Optional[str] = None,
) -> TransformResult:

    source_error = validate_profile_source(
        profile_text=profile_text,
    )

    if source_error:

        return (
            None,
            source_error,
        )

    source_hash = build_profile_source_hash(
        profile_text=profile_text,
        geography_1=geography_1,
        geography_2=geography_2,
        geography_3=geography_3,
        language=language,
    )

    prompt = build_profile_transformer_user_prompt(
        profile_text=profile_text,
        geography_1=geography_1,
        geography_2=geography_2,
        geography_3=geography_3,
        language=language,
    )

    raw_content = run_llm_json(
        prompt=prompt,
        model=model,
        temperature=0.0,
        system_prompt=(
            PROFILE_TRANSFORMER_SYSTEM_PROMPT
        ),
    )

    if not raw_content:

        return (
            None,
            (
                "Le moteur de transformation "
                "n'a retourné aucun résultat"
            ),
        )

    try:

        parsed_content = extract_json_object(
            raw_content
        )

        parsed_content[
            "schema_version"
        ] = PROFILE_SCHEMA_VERSION

        parsed_content[
            "language"
        ] = (
            language
            if language in {
                "fr",
                "en",
            }
            else "fr"
        )

        structured_profile = (
            StructuredUserProfile
            .parse_obj(
                parsed_content
            )
        )

        (
            structured_profile,
            resolution_warnings,
        ) = resolve_structured_profile_entities(
            structured_profile=structured_profile,
        )

    except ValidationError as exc:

        return (
            None,
            (
                "Le profil structuré ne respecte "
                f"pas le schéma : {exc}"
            ),
        )

    except ValueError as exc:

        return (
            None,
            str(exc),
        )

    warnings: List[str] = list(
        resolution_warnings
    )

    if not structured_profile.watch_instructions:

        warnings.append(
            "Aucune instruction de veille générée"
        )

    if not structured_profile.decision_lenses:

        warnings.append(
            "Aucun critère de décision généré"
        )

    result = ProfileTransformerResult(
        structured_profile=structured_profile,
        source_hash=source_hash,
        schema_version=PROFILE_SCHEMA_VERSION,
        transformer_version=(
            PROFILE_TRANSFORMER_VERSION
        ),
        warnings=warnings,
    )

    return (
        result,
        None,
    )
