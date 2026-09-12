import json

from typing import (
    Any,
    Dict,
    List,
    Optional,
)


# ============================================================
# VERSION
# ============================================================

PROFILE_ASSISTANT_VERSION = "1.0"

PROFILE_ASSISTANT_MAX_QUESTIONS = 5


# ============================================================
# SYSTEM PROMPT
# ============================================================

PROFILE_ASSISTANT_SYSTEM_PROMPT = """
You are the GetCurator profile assistant.

Your only mission is to help a user describe their professional
information needs precisely enough for GetCurator to:

1. identify content that belongs in their monitoring perimeter;
2. rank content according to their strategic priorities;
3. personalise the analysis contained in their Digests.

You are not a general-purpose assistant.
You are not producing market analysis.
You are not answering questions about current events.
You are helping construct a professional attention profile.


============================================================
BEHAVIOUR
============================================================

1. Read the existing profile, geographies, favourites and previous
   assistant conversation before deciding what to do.

2. Never ask for information that has already been supplied.

3. Ask only one question at a time.

4. Ask the question that would most improve future content selection.

5. Prefer concrete questions about:
   - the user's responsibilities;
   - the business perimeter they monitor;
   - why followed companies or topics matter;
   - strategic priorities;
   - relevant markets;
   - important business outcomes or metrics;
   - current versus future monitoring;
   - explicitly unwanted content.

6. Do not force every dimension to be completed.

7. Negative preferences are optional. Do not ask about them when
   higher-value information is missing.

8. Do not make the user classify information using technical
   categories or scoring weights.

9. Do not ask the user to distinguish between favourites and entities
   mentioned in their profile.

10. Favourites provide context, but they do not reveal why every
    company or topic matters.

11. When a broad favourite could create substantial noise, you may
    ask what aspects, markets or business questions matter.

12. Do not assume that every favourite is equally important.

13. Do not invent companies, markets, responsibilities, objectives,
    metrics or exclusions.

14. Preserve precise business terminology and recognised acronyms
    supplied by the user.

15. After enough information is available, stop asking questions and
    produce a complete profile proposal.

16. Never ask more than the allowed maximum number of questions.

17. If the existing profile is already detailed enough, propose an
    improved consolidated profile immediately.

18. The proposal must combine:
    - the existing profile;
    - useful information from the user's answers;
    - relevant context supplied by their favourites and geographies.

19. Do not mention internal JSON, databases, ranking engines,
    prompts or implementation details.

20. Respond only with one valid JSON object.
Do not include Markdown fences or text outside the JSON.
""".strip()


# ============================================================
# HELPERS
# ============================================================

def clean_optional_text(
    value: Optional[str],
) -> Optional[str]:

    if value is None:

        return None

    cleaned = value.strip()

    if not cleaned:

        return None

    return cleaned


def clean_string_list(
    values: Optional[List[str]],
) -> List[str]:

    if not values:

        return []

    result: List[str] = []

    seen = set()

    for value in values:

        if not isinstance(
            value,
            str,
        ):

            continue

        cleaned = value.strip()

        if not cleaned:

            continue

        normalized = (
            cleaned.casefold()
        )

        if normalized in seen:

            continue

        seen.add(
            normalized
        )

        result.append(
            cleaned
        )

    return result


def clean_messages(
    messages: Optional[List[Dict[str, Any]]],
) -> List[Dict[str, str]]:

    if not messages:

        return []

    result: List[Dict[str, str]] = []

    for message in messages:

        role = message.get(
            "role"
        )

        content = message.get(
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

        result.append(
            {
                "role": role,
                "content": cleaned_content,
            }
        )

    return result


# ============================================================
# COUNT QUESTIONS
# ============================================================

def count_assistant_questions(
    messages: List[Dict[str, str]],
) -> int:

    return sum(
        1
        for message in messages
        if (
            message["role"]
            == "assistant"
            and "?" in message["content"]
        )
    )


# ============================================================
# BUILD CONTEXT
# ============================================================

def build_profile_assistant_context(
    profile_text: Optional[str],
    geography_1: Optional[str] = None,
    geography_2: Optional[str] = None,
    geography_3: Optional[str] = None,
    companies: Optional[List[str]] = None,
    solutions: Optional[List[str]] = None,
    topics: Optional[List[str]] = None,
    messages: Optional[List[Dict[str, Any]]] = None,
    language: str = "fr",
) -> Dict[str, Any]:

    cleaned_messages = clean_messages(
        messages
    )

    return {
        "output_language": (
            language
            if language in {
                "fr",
                "en",
            }
            else "fr"
        ),
        "current_profile": (
            clean_optional_text(
                profile_text
            )
        ),
        "explicit_geographies": (
            clean_string_list(
                [
                    geography_1,
                    geography_2,
                    geography_3,
                ]
            )
        ),
        "followed_items": {
            "companies": (
                clean_string_list(
                    companies
                )
            ),
            "solutions": (
                clean_string_list(
                    solutions
                )
            ),
            "topics": (
                clean_string_list(
                    topics
                )
            ),
        },
        "conversation": (
            cleaned_messages
        ),
        "questions_already_asked": (
            count_assistant_questions(
                cleaned_messages
            )
        ),
        "maximum_questions": (
            PROFILE_ASSISTANT_MAX_QUESTIONS
        ),
    }


# ============================================================
# BUILD USER PROMPT
# ============================================================

def build_profile_assistant_user_prompt(
    profile_text: Optional[str],
    geography_1: Optional[str] = None,
    geography_2: Optional[str] = None,
    geography_3: Optional[str] = None,
    companies: Optional[List[str]] = None,
    solutions: Optional[List[str]] = None,
    topics: Optional[List[str]] = None,
    messages: Optional[List[Dict[str, Any]]] = None,
    language: str = "fr",
) -> str:

    context = build_profile_assistant_context(
        profile_text=profile_text,
        geography_1=geography_1,
        geography_2=geography_2,
        geography_3=geography_3,
        companies=companies,
        solutions=solutions,
        topics=topics,
        messages=messages,
        language=language,
    )

    questions_remaining = max(
        0,
        (
            PROFILE_ASSISTANT_MAX_QUESTIONS
            - context[
                "questions_already_asked"
            ]
        ),
    )

    return f"""
Evaluate the user's current profile information and decide whether
to ask one useful follow-up question or propose the final profile.

============================================================
CURRENT CONTEXT
============================================================

{json.dumps(
    context,
    ensure_ascii=False,
    indent=2,
)}

============================================================
QUESTIONS REMAINING
============================================================

{questions_remaining}


============================================================
DECISION
============================================================

Return action = "ASK" when one important clarification would
materially improve future content selection.

When action = "ASK":
- ask exactly one question;
- keep it concise and concrete;
- use the requested output language;
- proposed_profile_text must be null;
- profile_complete must be false.

Return action = "PROPOSE" when:
- the profile is sufficiently precise;
- another question would add only marginal value;
- or the maximum number of questions has been reached.

When action = "PROPOSE":
- message must briefly introduce the proposal;
- proposed_profile_text must contain the complete consolidated profile;
- profile_complete must be true.

The proposed profile must be a clear professional brief.
It may use short sections such as:
- Role and business context;
- Current focus;
- Strategic priorities;
- Markets;
- Future monitoring;
- Low-priority information.

Only include sections supported by the available information.

Do not copy a raw list of favourites without explaining their known
role. When their precise role is unknown, describe them neutrally as
followed actors or topics.

Do not include a "Low-priority information" section unless the user
has explicitly supplied exclusions.


============================================================
REQUIRED OUTPUT
============================================================

Return exactly:

{{
  "action": "ASK" or "PROPOSE",
  "message": "string",
  "proposed_profile_text": null or "complete profile",
  "profile_complete": false or true
}}
""".strip()
