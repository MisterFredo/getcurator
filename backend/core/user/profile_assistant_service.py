from typing import (
    Any,
    Dict,
    List,
    Optional,
    Tuple,
)

from pydantic import (
    ValidationError,
)

from core.user.profile_assistant_models import (
    ProfileAssistantResult,
)

from core.user.profile_assistant_prompt import (
    PROFILE_ASSISTANT_SYSTEM_PROMPT,
    PROFILE_ASSISTANT_VERSION,
    build_profile_assistant_user_prompt,
)

from core.user.profile_transformer_service import (
    extract_json_object,
)

from core.user.user_preferences_service import (
    get_user_preferences_detailed,
)

from core.user.user_profile_service import (
    get_user_profile,
)

from utils.llm import (
    run_llm_json,
)


# ============================================================
# TYPES
# ============================================================

AssistantServiceResult = Tuple[
    Optional[Dict[str, Any]],
    Optional[str],
]


# ============================================================
# EXTRACT LABELS
# ============================================================

def extract_labels(
    items: Optional[List[Dict[str, Any]]],
) -> List[str]:

    if not items:

        return []

    labels: List[str] = []

    seen = set()

    for item in items:

        label = item.get(
            "label"
        )

        if not isinstance(
            label,
            str,
        ):

            continue

        cleaned_label = (
            label.strip()
        )

        if not cleaned_label:

            continue

        normalized_label = (
            cleaned_label.casefold()
        )

        if normalized_label in seen:

            continue

        seen.add(
            normalized_label
        )

        labels.append(
            cleaned_label
        )

    return labels


# ============================================================
# NORMALIZE MESSAGES
# ============================================================

def normalize_assistant_messages(
    messages: Optional[List[Any]],
) -> List[Dict[str, str]]:

    if not messages:

        return []

    normalized_messages: List[
        Dict[str, str]
    ] = []

    for message in messages:

        if hasattr(
            message,
            "dict",
        ):

            message_data = (
                message.dict()
            )

        elif isinstance(
            message,
            dict,
        ):

            message_data = message

        else:

            continue

        role = message_data.get(
            "role"
        )

        content = message_data.get(
            "content"
        )

        if role not in {
            "user",
            "assistant",
        }:

            continue

        if not isinstance(
            content,
            str,
        ):

            continue

        cleaned_content = (
            content.strip()
        )

        if not cleaned_content:

            continue

        normalized_messages.append(
            {
                "role": role,
                "content": cleaned_content,
            }
        )

    return normalized_messages


# ============================================================
# RUN PROFILE ASSISTANT
# ============================================================

def run_profile_assistant(
    user_id: str,
    messages: Optional[List[Any]] = None,
    language: str = "fr",
    model: Optional[str] = None,
    account_context: Optional[
        Dict[str, Any]
    ] = None,
) -> AssistantServiceResult:

    if not user_id:

        return (
            None,
            "user_id manquant",
        )

    current_profile = (
        get_user_profile(
            user_id=user_id,
        )
        or {}
    )

    preferences = (
        get_user_preferences_detailed(
            user_id=user_id,
        )
        or {}
    )

    normalized_messages = (
        normalize_assistant_messages(
            messages=messages,
        )
    )

    companies = extract_labels(
        preferences.get(
            "companies"
        )
    )

    solutions = extract_labels(
        preferences.get(
            "solutions"
        )
    )

    topics = extract_labels(
        preferences.get(
            "topics"
        )
    )

    prompt = (
        build_profile_assistant_user_prompt(
            profile_text=(
                current_profile.get(
                    "profile_text"
                )
            ),
            geography_1=(
                current_profile.get(
                    "geography_1"
                )
            ),
            geography_2=(
                current_profile.get(
                    "geography_2"
                )
            ),
            geography_3=(
                current_profile.get(
                    "geography_3"
                )
            ),
            companies=companies,
            solutions=solutions,
            topics=topics,
            messages=normalized_messages,
            language=language,
            account_context=account_context,
        )
    )
    
    raw_content = run_llm_json(
        prompt=prompt,
        model=model,
        temperature=0.1,
        system_prompt=(
            PROFILE_ASSISTANT_SYSTEM_PROMPT
        ),
    )

    if not raw_content:

        return (
            None,
            (
                "L'assistant de profil "
                "n'a retourné aucun résultat"
            ),
        )

    try:

        parsed_content = (
            extract_json_object(
                raw_content
            )
        )

        assistant_result = (
            ProfileAssistantResult
            .parse_obj(
                parsed_content
            )
        )

    except ValidationError as error:

        return (
            None,
            (
                "Réponse invalide de "
                f"l'assistant de profil : {error}"
            ),
        )

    except ValueError as error:

        return (
            None,
            str(error),
        )

    return (
        {
            "status": "ok",
            "assistant_version": (
                PROFILE_ASSISTANT_VERSION
            ),
            "action": (
                assistant_result.action
            ),
            "message": (
                assistant_result.message
            ),
            "proposed_profile_text": (
                assistant_result
                .proposed_profile_text
            ),
            "profile_complete": (
                assistant_result
                .profile_complete
            ),
        },
        None,
    )
