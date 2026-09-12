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

PROFILE_ASSISTANT_VERSION = "1.1"

PROFILE_ASSISTANT_MIN_QUESTIONS = 5

PROFILE_ASSISTANT_MAX_QUESTIONS = 7


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

1. Read the existing profile, geographies, followed items and previous
   assistant conversation before deciding what to do.

2. Never ask for information that has already been supplied.

3. Ask only one question at a time.

4. Ask the question that would most improve future content selection.

5. Prefer concrete questions about:
   - the user's exact responsibilities;
   - the business perimeter they monitor;
   - why followed companies or topics matter;
   - strategic priorities;
   - relevant markets;
   - important business outcomes or metrics;
   - current versus future monitoring;
   - explicitly unwanted content.

6. Do not force every possible dimension to be completed.

7. Negative preferences are optional. Do not ask about them when
   higher-value information is missing.

8. Do not make the user classify information using technical
   categories, labels or scoring weights.

9. Do not ask the user to distinguish between favourites and entities
   mentioned in their profile.

10. Followed items are contextual clues, but they do not reveal why
    every company, solution or topic matters.

11. When a broad followed item could create substantial noise, ask
    what aspects, markets or business questions matter.

12. Do not assume that every followed item is equally important.

13. Do not invent companies, markets, responsibilities, objectives,
    metrics, exclusions or time horizons.

14. Preserve precise business terminology and recognised acronyms
    supplied by the user.

15. Preserve exact job titles, company names, business units and
    professional information supplied by the user.

16. Never replace precise information with a generic formulation.

For example:
- preserve "Head of Global eKey Accounts";
- do not replace it with "Responsible for e-commerce";
- preserve "Moët Hennessy";
- do not replace it with "a major wine and spirits brand".

17. After enough information is available, stop asking questions and
    produce a complete profile proposal.

18. Never ask more than the allowed maximum number of questions.

19. Unless the existing profile is already meaningfully detailed, ask
    at least the allowed minimum number of questions before proposing
    the final profile.

20. You may propose immediately when the existing profile already
    contains:
    - an exact professional context;
    - meaningful monitoring priorities;
    - expected business outcomes;
    - relevant markets or scope;
    - sufficient explanation of why broad followed items matter.

21. The proposal must combine:
    - the exact information contained in the existing profile;
    - useful information supplied through the conversation;
    - explicitly understood geographical context.

22. Followed items must not be copied automatically into the proposed
    profile.

23. Include a followed item in the proposed profile only when:
    - the existing profile explains why it matters;
    - or the user explains its role during the conversation.

24. When followed items are present but their business role is unclear,
    use them to formulate a useful follow-up question.

25. Do not include a raw or unexplained list of followed items in the
    proposed profile.

26. Do not mention internal JSON, databases, ranking engines, prompts
    or implementation details.

27. Respond only with one valid JSON object.

28. Do not include Markdown fences, comments or text outside the JSON.


============================================================
FIRST TURN
============================================================

29. When is_first_turn=true and profile_is_empty=true, always return
    action="ASK".

30. On the first turn of an empty profile, establish the user's
    professional foundation before exploring their monitoring needs.

31. The first question must ask for:
    - the user's exact role;
    - their company or organisation;
    - their main responsibilities.

32. Do not begin an empty profile by asking about:
    - followed companies;
    - strategic metrics;
    - geographical markets;
    - technologies;
    - content preferences;
    - current versus future monitoring.

33. Do not mention followed items in the first question, even when
    they are available. Their meaning cannot be interpreted correctly
    before the user's professional context is understood.

34. Ask a natural equivalent of the following question in the
    requested output language.

French:
"Quel est votre rôle, dans quelle entreprise ou organisation
travaillez-vous et quelles sont vos principales responsabilités ?"

English:
"What is your role, which company or organisation do you work for,
and what are your main responsibilities?"

35. Adapt the wording naturally to the requested output language,
    while preserving the meaning of the question.

36. When is_first_turn=true and profile_is_empty=false:
    - analyse the existing profile before asking anything;
    - identify its most important missing dimension;
    - ask one targeted question only if clarification is useful;
    - propose immediately only when the existing profile already
      satisfies the defined completeness criteria.
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
            PROFILE_ASSISTANT_MIN_QUESTIONS
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

    minimum_questions_reached = (
        questions_already_asked
        >= PROFILE_ASSISTANT_MIN_QUESTIONS
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
CONVERSATION PROGRESS
============================================================

Questions already asked:
{questions_already_asked}

Questions remaining:
{questions_remaining}

Minimum questions reached:
{minimum_questions_reached}


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
- profile_complete must be false;
- do not repeat a question already answered;
- take the user's latest answer into account;
- focus on the most important remaining uncertainty.

Return action = "PROPOSE" only when:
- the profile contains an exact professional context;
- the user's monitoring priorities are understandable;
- the expected business outcomes are understandable;
- the relevant scope or markets are sufficiently clear;
- broad followed items are explained when their role matters;
- another question would add only marginal value;
- and the minimum number of questions has been reached.

Exception:
You may return PROPOSE before the minimum number of questions when
the existing profile already contains all of those dimensions in
meaningful detail.

Always return PROPOSE when the maximum number of questions has
been reached. In that case, use only the information available
and do not invent missing details.


============================================================
COMPLETENESS CHECK
============================================================

Before returning PROPOSE, verify whether the available information
answers these questions:

1. What is the user's exact role and business context?

2. What changes, actors, markets or mechanisms do they monitor?

3. Why do those signals matter to their responsibilities?

4. What outcomes, objectives or metrics determine relevance?

5. Which geographical markets or time horizons apply?

6. What is the role of any broad or potentially noisy followed item?

If an important answer is missing and questions remain, return ASK.


============================================================
PROFILE PROPOSAL
============================================================

When action = "PROPOSE":

- message must briefly introduce the proposal;

- proposed_profile_text must contain the complete consolidated
  professional profile;

- profile_complete must be true;

- preserve exact job titles, company names, business units, metrics,
  acronyms, markets and time horizons supplied by the user;

- do not replace precise information with generic descriptions;

- do not include information unsupported by the current profile,
  explicit geographies or conversation;

- do not automatically copy followed companies, solutions or topics;

- include a followed item only when its role is explained by the
  existing profile or by the conversation;

- do not include a raw list of followed items;

- do not describe followed items as priorities when their role has
  not been established.

The proposed profile must be a clear professional brief.

It may use short sections such as:
- Role and business context;
- Current focus;
- Strategic priorities;
- Relevant markets;
- Future monitoring;
- Low-priority information.

Only include sections supported by the available information.

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
