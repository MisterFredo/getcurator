import hashlib
import json

from typing import (
    Any,
    Dict,
    List,
    Optional,
)

from utils.llm import (
    run_llm,
)

from core.user.profile_editorial_prompt import (
    PROFILE_EDITORIAL_SYSTEM_PROMPT,
    PROFILE_EDITORIAL_TRANSFORMER_VERSION,
    build_profile_editorial_source_payload,
    build_profile_editorial_user_prompt,
)

from core.user.user_profile_service import (
    mark_profile_editorial_building,
    record_profile_editorial_transformation_error,
    save_editorial_user_profile,
)


# ============================================================
# CONFIGURATION
# ============================================================

PROFILE_EDITORIAL_TEMPERATURE = 0.0


# ============================================================
# CLEAN GENERATED TEXT
# ============================================================

def _clean_generated_editorial_text(
    value: Optional[str],
) -> str:

    if not isinstance(
        value,
        str,
    ):

        return ""

    cleaned = value.strip()

    # Defensive cleanup in case the model returns
    # a Markdown fence despite the prompt.
    if cleaned.startswith(
        "```"
    ):

        lines = cleaned.splitlines()

        if lines:

            lines = lines[1:]

        if (
            lines
            and lines[-1].strip() == "```"
        ):

            lines = lines[:-1]

        cleaned = "\n".join(
            lines
        ).strip()

    return cleaned


# ============================================================
# BUILD SOURCE HASH
# ============================================================

def build_profile_editorial_source_hash(
    profile_text: str,
    geography_1: Optional[str] = None,
    geography_2: Optional[str] = None,
    geography_3: Optional[str] = None,
    companies: Optional[List[str]] = None,
    solutions: Optional[List[str]] = None,
    topics: Optional[List[str]] = None,
    language: str = "fr",
    account_context: Optional[
        Dict[str, Any]
    ] = None,
) -> str:
    """
    Build a stable hash from the exact normalized payload
    used to generate the editorial profile and its prompt version.
    """

    source_payload = (
        build_profile_editorial_source_payload(
            profile_text=profile_text,
            geography_1=geography_1,
            geography_2=geography_2,
            geography_3=geography_3,
            companies=companies,
            solutions=solutions,
            topics=topics,
            language=language,
            account_context=account_context,
        )
    )

    # Invalidate the cached editorial profile when the prompt changes.
    hash_payload = {
        "transformer_version": (
            PROFILE_EDITORIAL_TRANSFORMER_VERSION
        ),
        "source_payload": source_payload,
    }

    serialized_payload = json.dumps(
        hash_payload,
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
# BUILD COMPLETE PROMPT
# ============================================================

def _build_complete_editorial_prompt(
    profile_text: str,
    geography_1: Optional[str] = None,
    geography_2: Optional[str] = None,
    geography_3: Optional[str] = None,
    companies: Optional[List[str]] = None,
    solutions: Optional[List[str]] = None,
    topics: Optional[List[str]] = None,
    language: str = "fr",
    account_context: Optional[
        Dict[str, Any]
    ] = None,
) -> str:

    user_prompt = (
        build_profile_editorial_user_prompt(
            profile_text=profile_text,
            geography_1=geography_1,
            geography_2=geography_2,
            geography_3=geography_3,
            companies=companies,
            solutions=solutions,
            topics=topics,
            language=language,
            account_context=account_context,
        )
    )

    return f"""
{PROFILE_EDITORIAL_SYSTEM_PROMPT}


============================================================
TASK
============================================================

{user_prompt}
""".strip()


# ============================================================
# GENERATE EDITORIAL PROFILE
# ============================================================

def generate_profile_editorial_text(
    profile_text: str,
    geography_1: Optional[str] = None,
    geography_2: Optional[str] = None,
    geography_3: Optional[str] = None,
    companies: Optional[List[str]] = None,
    solutions: Optional[List[str]] = None,
    topics: Optional[List[str]] = None,
    language: str = "fr",
    account_context: Optional[
        Dict[str, Any]
    ] = None,
) -> str:
    """
    Generate one extended editorial profile without
    writing anything to BigQuery.
    """

    prompt = (
        _build_complete_editorial_prompt(
            profile_text=profile_text,
            geography_1=geography_1,
            geography_2=geography_2,
            geography_3=geography_3,
            companies=companies,
            solutions=solutions,
            topics=topics,
            language=language,
            account_context=account_context,
        )
    )

    result = run_llm(
        prompt=prompt,
        temperature=(
            PROFILE_EDITORIAL_TEMPERATURE
        ),
    )

    editorial_text = (
        _clean_generated_editorial_text(
            result
        )
    )

    if not editorial_text:

        raise ValueError(
            "The editorial profile transformation "
            "returned an empty result."
        )

    return editorial_text


# ============================================================
# BUILD EDITORIAL PROFILE
# ============================================================

def build_profile_editorial_result(
    profile_text: str,
    geography_1: Optional[str] = None,
    geography_2: Optional[str] = None,
    geography_3: Optional[str] = None,
    companies: Optional[List[str]] = None,
    solutions: Optional[List[str]] = None,
    topics: Optional[List[str]] = None,
    language: str = "fr",
    account_context: Optional[
        Dict[str, Any]
    ] = None,
) -> Dict[str, str]:
    """
    Generate the editorial profile and return the
    complete persistence metadata.
    """

    source_hash = (
        build_profile_editorial_source_hash(
            profile_text=profile_text,
            geography_1=geography_1,
            geography_2=geography_2,
            geography_3=geography_3,
            companies=companies,
            solutions=solutions,
            topics=topics,
            language=language,
            account_context=account_context,
        )
    )

    editorial_text = (
        generate_profile_editorial_text(
            profile_text=profile_text,
            geography_1=geography_1,
            geography_2=geography_2,
            geography_3=geography_3,
            companies=companies,
            solutions=solutions,
            topics=topics,
            language=language,
            account_context=account_context,
        )
    )

    return {

        "editorial_text":
            editorial_text,

        "source_hash":
            source_hash,

        "transformer_version":
            (
                PROFILE_EDITORIAL_TRANSFORMER_VERSION
            ),

    }


# ============================================================
# GENERATE AND SAVE EDITORIAL PROFILE
# ============================================================

def generate_and_save_profile_editorial(
    user_id: str,
    profile_text: str,
    geography_1: Optional[str] = None,
    geography_2: Optional[str] = None,
    geography_3: Optional[str] = None,
    companies: Optional[List[str]] = None,
    solutions: Optional[List[str]] = None,
    topics: Optional[List[str]] = None,
    language: str = "fr",
    account_context: Optional[
        Dict[str, Any]
    ] = None,
) -> Dict[str, str]:
    """
    Generate and persist one extended editorial profile.

    The existing editorial profile is preserved when
    generation fails.
    """

    mark_profile_editorial_building(
        user_id=user_id,
    )

    try:

        result = (
            build_profile_editorial_result(
                profile_text=profile_text,
                geography_1=geography_1,
                geography_2=geography_2,
                geography_3=geography_3,
                companies=companies,
                solutions=solutions,
                topics=topics,
                language=language,
                account_context=account_context,
            )
        )

        save_editorial_user_profile(
            user_id=user_id,
            editorial_text=(
                result[
                    "editorial_text"
                ]
            ),
            source_hash=(
                result[
                    "source_hash"
                ]
            ),
            transformer_version=(
                result[
                    "transformer_version"
                ]
            ),
        )

        return result

    except Exception as exc:

        record_profile_editorial_transformation_error(
            user_id=user_id,
            error=str(
                exc
            ),
        )

        raise
