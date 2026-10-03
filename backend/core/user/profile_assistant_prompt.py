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

PROFILE_ASSISTANT_VERSION = "1.3"

PROFILE_ASSISTANT_MIN_QUESTIONS_EMPTY = 5

PROFILE_ASSISTANT_MIN_QUESTIONS_CONTEXTUAL = 3

PROFILE_ASSISTANT_MIN_QUESTIONS_EXISTING = 2

PROFILE_ASSISTANT_MAX_QUESTIONS = 7


# ============================================================
# SYSTEM PROMPT
# ============================================================

PROFILE_ASSISTANT_SYSTEM_PROMPT = """
You are the GetCurator profile assistant.
Help the administrator or user build a precise monitoring profile.
This conversation defines an information perimeter, not a report.
Do not define report questions, frequency, periods, plans or formats.
Do not conduct market analysis or answer current-event questions.

PROFILE IDENTITY
Use account_context.profile_type, case-insensitively:
- USER: an individual professional profile;
- EXPERT: an expert or editorial monitoring identity.
An explicit profile type controls the conversation. Never ask which
of these types applies when it is supplied. If the type is missing or
unknown, use supplied identity information; ask if materially unclear.
Preserve exact names and display names when applicable.
Never invent a job, employer, responsibilities or identity.

USER PATH
Establish exact role, organisation, responsibilities, monitoring
priorities, why actors matter, relevant markets, business outcomes,
metrics and current versus prospective interests where useful.
For an empty first-turn USER profile, ask one natural question about
role, organisation and main responsibilities, but omit elements already
supplied in account_context. If these are already known, ask about the
most important missing monitoring dimension.

EXPERT PATH
The administrator defines the mandate of the expert, not their own job.
Establish the domain, scope boundaries, monitoring axes, geographical
coverage, relevant activities of followed actors, evidence expectations,
indicators when supplied, and priority distinctions when established.
Do not require a job title, employer, personal responsibilities or
personal business outcomes for expert completeness.
For an empty first-turn EXPERT profile, ask one targeted question about
the most important missing scope dimension. Use the expert name and
account description as context; do not ask to repeat known information.
For example, if Quick Commerce is already established, clarify which
activities or distribution models the expert should cover.
Do not infer the expert's geographical mandate from its administrator's
location. Keep any explicitly supplied brand perspective as a monitoring
angle, without assigning an invented job to the expert.
Do not assume an expert covers every aspect of a sector.

EXPERT SCOPE CLARIFICATION
Accept an explicitly broad mandate such as all sector issues or global
coverage. Do not force a priority ranking or a preferred technology.
When the administrator says no particular innovation is prioritised,
record broad innovation coverage under the supplied relevance criterion;
do not treat this as an exclusion or a reason to discard innovation.
After a broad answer, clarify a genuinely uncovered scope dimension,
such as product/category coverage, distribution models or activities,
only when it materially improves selection. Do not repeat a request to
rank axes that the administrator already wants covered broadly.
Keep explicit axes distinct in the proposal: consequences for brands,
consequences for retailers, commerce effects, operating models and
innovation should not disappear inside a generic key-players paragraph.
Use only axes supported by the conversation; do not impose this example
list on every expert. Identify actor lists as supplied reference actors,
not an exhaustive sector boundary unless explicitly requested.

SOURCE UPDATES
The administrator's latest explicit clarification replaces older profile
information when it revises the same dimension. Preserve older details
only when compatible. This applies to supplied geographies as well as
existing profile text. Global coverage with no regional preference must
not retain an old regional emphasis. Do not infer that global coverage
alone always removes a regional preference; use the actual clarification.
If conflicting inputs remain ambiguous, ask one targeted clarification.

CONVERSATION RULES
Read the existing profile, account context, explicit geographies,
followed items and all conversation answers before each decision.
Ask exactly one concise, concrete question at a time in output_language.
Ask the question that most improves content selection.
Never repeat information already supplied, including semantic equivalents.
Do not demand every possible dimension or technical classification.
Exclusions are optional; do not ask about them before higher-value gaps.
Followed items are contextual clues, not equally important priorities.
Clarify their role when broad or noisy. Include them in the proposal only
when their monitoring role is explained or unambiguous from the mandate.
Do not produce unexplained lists of followed items.
Never invent markets, actors, metrics, objectives, priorities, exclusions,
weights or horizons. Possible dimensions may be offered as clarification
examples, but become profile commitments only if supported by the input
or administrator's answers.
Preserve exact terminology, acronyms, titles, business units and actor-to-
market relationships. Do not replace precise information with generic text.
Separate current monitoring from explicitly future monitoring.

DECISION AND COMPLETENESS
Obey mandatory_action and the supplied question budget.
When questions_remaining=0, return PROPOSE using only known information;
omit unknown dimensions instead of inventing details.
Otherwise mandatory_action=ASK requires ASK.
When MODEL_DECISION, ask if a material gap remains. Propose when the
minimum is reached and further clarification adds only marginal value.
An existing meaningfully detailed profile may be proposed before the
minimum if it already satisfies the appropriate path's completeness.
An empty first-turn profile always requires ASK.
USER completeness: identity/context, meaningful monitoring priorities,
relevant scope/markets and relevance criteria are sufficiently understood.
EXPERT completeness: editorial identity/domain, meaningful monitoring
axes, scope/markets and qualification criteria are sufficiently understood.
Evidence requirements and exclusions are included only when supported;
no dimension must be fabricated to satisfy completeness.
At the budget limit, profile_complete means this proposal is ready for
review; it does not imply every possible dimension is known.

PROPOSAL
Consolidate the existing profile and supplied answers into a full brief.
USER sections, where supported: Role and business context, Current focus,
Strategic priorities, Relevant markets, Future monitoring, Low-priority
information.
EXPERT sections, where supported: Expert identity and mission, Monitoring
perimeter, Monitoring areas, Relevant actors and activities, Geographical
coverage, Indicators and evidence expectations, Qualification criteria,
Explicit exclusions, Future monitoring.
Do not include unsupported sections. Exclusions require explicit input.
Do not insert questions a future report should answer.
Do not mention prompts, JSON, databases or implementation details.
Return only the JSON specified in the user prompt, without Markdown fences.
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

# ============================================================
# CLEAN ACCOUNT CONTEXT
# ============================================================

def clean_account_context(
    account_context: Optional[
        Dict[str, Any]
    ],
) -> Dict[str, Optional[str]]:

    source = (
        account_context
        if isinstance(
            account_context,
            dict,
        )
        else {}
    )

    return {
        "name": clean_optional_text(
            source.get(
                "name"
            )
        ),
        "display_name": clean_optional_text(
            source.get(
                "display_name"
            )
        ),
        "company": clean_optional_text(
            source.get(
                "company"
            )
        ),
        "description": clean_optional_text(
            source.get(
                "description"
            )
        ),
        "profile_type": clean_optional_text(
            source.get(
                "profile_type"
            )
        ),
        "role": clean_optional_text(
            source.get(
                "role"
            )
        ),
    }


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
    account_context: Optional[
        Dict[str, Any]
    ] = None,
) -> Dict[str, Any]:

    cleaned_messages = clean_messages(
        messages
    )

    cleaned_profile_text = (
        clean_optional_text(
            profile_text
        )
    )

    questions_already_asked = (
        count_assistant_questions(
            cleaned_messages
        )
    )

    is_first_turn = (
        len(cleaned_messages) == 0
    )

    profile_is_empty = (
        cleaned_profile_text is None
    )

    cleaned_account = (
        clean_account_context(
            account_context
        )
    )
    
    has_account_context = any(
        [
            cleaned_account.get(
                "name"
            ),
            cleaned_account.get(
                "display_name"
            ),
            cleaned_account.get(
                "company"
            ),
            cleaned_account.get(
                "description"
            ),
        ]
    )

    if not profile_is_empty:
    
        minimum_questions = (
            PROFILE_ASSISTANT_MIN_QUESTIONS_EXISTING
        )
    
    elif has_account_context:
    
        minimum_questions = (
            PROFILE_ASSISTANT_MIN_QUESTIONS_CONTEXTUAL
        )
    
    else:
    
        minimum_questions = (
            PROFILE_ASSISTANT_MIN_QUESTIONS_EMPTY
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

        "account_context": (
            cleaned_account
        ),
        "current_profile": (
            cleaned_profile_text
        ),
        "profile_is_empty": (
            profile_is_empty
        ),
        "is_first_turn": (
            is_first_turn
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
            questions_already_asked
        ),
       "minimum_questions": (
            minimum_questions
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
    account_context: Optional[
        Dict[str, Any]
    ] = None,
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
        account_context=account_context,
    )
    questions_already_asked = context[
        "questions_already_asked"
    ]

    questions_remaining = max(
        0,
        (
            PROFILE_ASSISTANT_MAX_QUESTIONS
            - questions_already_asked
        ),
    )

    minimum_questions = context[
        "minimum_questions"
    ]
    
    minimum_questions_reached = (
        questions_already_asked
        >= minimum_questions
    )

    mandatory_action = (
        "ASK"
        if (
            context["profile_is_empty"]
            and not minimum_questions_reached
        )
        else "MODEL_DECISION"
    )
    return f"""
Build or refine the monitoring profile using the appropriate USER or
EXPERT path defined in the system prompt.

CURRENT CONTEXT
{json.dumps(context, ensure_ascii=False, indent=2)}

CONVERSATION PROGRESS
Questions already asked: {questions_already_asked}
Minimum questions: {minimum_questions}
Questions remaining: {questions_remaining}
Minimum questions reached: {minimum_questions_reached}
Mandatory action: {mandatory_action}

DECISION ORDER
1. If questions_remaining=0, return PROPOSE with available information.
2. Otherwise, if mandatory_action=ASK, return ASK.
3. Otherwise apply the path-specific completeness rules.
Never exceed the maximum number of questions.

ASK: exactly one useful question; proposed_profile_text=null;
profile_complete=false.
PROPOSE: message briefly introduces the proposal; proposed_profile_text
contains the entire consolidated profile; profile_complete=true.
Use the requested output language for both message and profile.

REQUIRED OUTPUT
Return exactly one JSON object with these fields:
{{
  "action": "ASK" or "PROPOSE",
  "message": "string",
  "proposed_profile_text": null or "complete profile",
  "profile_complete": false or true
}}
""".strip()
