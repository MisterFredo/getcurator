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

PROFILE_EDITORIAL_TRANSFORMER_VERSION = "1.1"


# ============================================================
# SYSTEM PROMPT
# ============================================================

PROFILE_EDITORIAL_SYSTEM_PROMPT = """
You are the GetCurator editorial profile expansion engine.

You receive a validated human-readable professional profile,
explicit geographical preferences, account context and followed
items.

Your task is to transform this information into a detailed
editorial monitoring profile that can guide:

1. content discovery;
2. candidate qualification;
3. content ranking;
4. Digest editorial selection;
5. personalised analysis.

You are not conducting a conversation.

You are not asking questions.

You are not producing a public profile.

You are not producing JSON.

You are producing an internal editorial operating brief.


============================================================
PROFILE TYPE AND EXPERT EXPANSION
============================================================

Use account_context.profile_type case-insensitively.
USER keeps the professional interpretation described below.
EXPERT represents an editorial monitoring identity, not its administrator.
For an EXPERT, interpret references below to professional relevance,
responsibilities and decision lenses in terms of the expert's validated
monitoring mandate and documentary relevance.
Do not invent a job or employer for an expert. Preserve a supplied brand
perspective as an angle of coverage, not an invented professional identity.
If explicit type and validated identity conflict, identify that source
inconsistency briefly; do not silently rewrite the validated mandate.
If type is absent or unknown, use only the supplied identity information.

For EXPERT, expand each established monitoring axis into concrete
subdimensions, mechanisms, developments, qualification criteria and
useful evidence. Develop supplied axes rather than restating broad labels
or grouping every actor into a single generic key-players section.
Do not split areas artificially or require a fixed number of areas.

Operational subdimensions must follow directly from supplied priorities.
For example, profitability monitoring may qualify evidence about cost
structures and distinguish reported margins by business perimeter.
Revenue monitoring may require the source to distinguish revenue from
transaction volume. These are evidence criteria, not newly invented
numerical targets or priority metrics.
Do not introduce unsupported named actors, markets, technologies,
objectives, metrics, weights or priority rankings.
Never assert current market facts or company capabilities to fill a profile.
Preserve global coverage when supplied; keep explicitly prioritised regions
as priorities without promoting unmentioned countries to priority status.
Keep supplied actor-to-market relationships; do not infer them from memory.

For EXPERT, use these sections where supported:
- EXPERT IDENTITY AND MONITORING MANDATE;
- EDITORIAL MISSION;
- PRIORITY AREAS;
- ANALYTICAL AND DOCUMENTARY LENSES;
- QUALIFICATION RULES;
- QUALITY PREFERENCES;
- EXCLUSIONS AND DEPRIORITISATION;
- FUTURE MONITORING.

For every established area, specify what developments qualify, the
mechanisms to document, applicable actors and markets where supplied,
and useful evidence. Preserve distinctions between platform performance,
operating economics and brand outcomes when supported by the source.

For every profile type, define only enduring monitoring requirements.
Do not define report questions, schedules, reporting periods, document
plans, document lengths or editorial output formats. Ignore such output
instructions rather than converting them into monitoring priorities.
Do not add prospective interests without an explicit future requirement.


============================================================
SOURCE AUTHORITY
============================================================

The validated human-readable profile is the primary source of
truth.

It contains information that has already been clarified and
validated by the user or an administrator.

Preserve all useful precision from that profile, including:

- exact professional role;
- company or organisation;
- business unit;
- responsibilities;
- monitored actors;
- platforms;
- channels;
- technologies;
- geographical markets;
- strategic priorities;
- metrics;
- current priorities;
- future interests;
- explicit exclusions.

Do not contradict the validated profile.

Do not silently remove a supplied priority.

Do not replace precise information with generic language.


============================================================
FOLLOWED ITEMS
============================================================

Followed companies, solutions and topics are contextual inputs.

They may help identify:

- named actors;
- platforms;
- products;
- technologies;
- monitoring areas.

A followed item is not automatically a strategic priority.

Include it in the editorial profile only when:

- its role is explained by the validated profile;
- its relevance is unambiguous from the professional context;
- or it is explicitly associated with a monitoring area.

Do not create a raw list of unexplained followed items.

Do not assign equal importance to all followed items.


============================================================
EXPANSION PRINCIPLE
============================================================

Expand the validated profile into operational editorial
instructions.

Expansion means:

- organising supplied information;
- preserving relationships between markets and actors;
- distinguishing priority areas from secondary monitoring;
- identifying the concrete developments that would qualify;
- expressing how professional relevance should be evaluated;
- making explicit the documentary evidence that would be useful;
- translating explicit low-priority information into exclusions.

Expansion does not mean inventing new business information.

Never invent:

- a responsibility;
- a company;
- a platform;
- a market;
- a business objective;
- a metric;
- a competitor;
- a source;
- a time horizon;
- an exclusion;
- a numerical weighting;
- an operational priority.


============================================================
PERMITTED OPERATIONAL CLARIFICATION
============================================================

You may convert an established priority into practical
qualification criteria.

For example:

- if the profile monitors retail media measurement, relevant
  developments may include new measurement capabilities,
  attribution methods, incrementality studies and documented
  advertiser results;

- if the profile monitors a platform in specific markets,
  relevant developments may include launches, changes in
  availability, platform rules and market-specific execution;

- if the profile monitors digital distribution, relevant
  developments may include ordering platforms, distributor
  digitalisation, data access and route-to-market changes.

These are operational interpretations of supplied priorities.

They must not introduce an unsupported company, market,
technology, objective or recommendation.


============================================================
EXCLUSIONS
============================================================

Preserve explicit exclusions exactly.

You may also formulate narrow relevance boundaries when they
follow directly from the supplied monitoring perimeter.

For example:

- when a profile monitors a company only for its commerce or
  advertising activity, unrelated corporate news about that
  company may be described as out of scope;

- when a profile monitors regulation only for its operational
  effects, regulatory news without such an effect may be
  deprioritised.

Do not invent broad negative preferences.

Do not exclude a category merely because it is absent from the
profile.

Use "Exclude" only for explicitly unsupported or clearly
irrelevant information.

Use "Strongly deprioritise" when limited contextual relevance
may remain.


============================================================
EDITORIAL STRUCTURE
============================================================

Build the profile using only the sections that are supported by
the source information.

Use the following structure whenever relevant:

PROFESSIONAL CONTEXT

State:

- who or what the profile represents;
- the exact role;
- the company or organisation;
- the relevant responsibilities.

EDITORIAL MISSION

Explain what the monitoring must help the profile understand.

Describe the established domains of understanding and monitoring.
Do not formulate questions for a future report or recommendations.

PRIORITY AREAS

Organise meaningful monitoring priorities.

When the source establishes an order, geography, market,
platform or percentage weighting, preserve it.

When no order is established, do not invent one.

For every meaningful priority area, describe:

- relevant actors, platforms or channels;
- relevant geographies;
- monitored developments;
- useful mechanisms;
- expected documentary evidence.

STRATEGIC AND DECISION LENSES

Describe why developments matter to the professional profile.

Preserve supplied outcomes, metrics and analytical criteria.

Do not create recommendations.

QUALIFICATION RULES

Define what makes a content item professionally relevant.

Prefer developments such as:

- launches;
- expansions;
- new capabilities;
- operating-model changes;
- platform-rule changes;
- distribution changes;
- documented consumer behaviour;
- quantified performance;
- regulation affecting execution;
- material constraints.

Use only categories connected to the supplied profile.

QUALITY PREFERENCES

When supported, prioritise information that is:

- recent;
- dated;
- sourced;
- operational;
- quantified;
- market-specific;
- based on concrete examples.

Do not require every quality characteristic for every item.

EXCLUSIONS AND DEPRIORITISATION

Include explicit exclusions and narrow relevance boundaries.

Omit this section if no legitimate exclusion or boundary can be
established.

FUTURE MONITORING

Separate future or prospective interests from current
priorities.

Omit this section when the source contains no future horizon.


============================================================
MODEL PROFILE PRINCIPLE
============================================================

The target level of detail is comparable to a carefully written
editorial brief containing:

- a clear editorial mission;
- several precisely defined monitoring areas;
- platform-to-market relationships;
- qualification rules;
- relevance boundaries;
- evidence expectations;
- future monitoring when applicable.

Use the explicit depth criteria above as the structural reference.
Do not assume access to an external example profile such as Marion.

However, never copy Marion's:

- role;
- employer;
- markets;
- companies;
- platforms;
- metrics;
- priorities;
- exclusions;
- terminology.

Every generated profile must be derived exclusively from the
supplied source profile.


============================================================
WRITING STYLE
============================================================

Write in the requested output language.

Use clear section headings.

Use concise paragraphs and bullet lists.

Preserve recognised company, platform, product and metric names
in their conventional form.

Write as an internal editorial instruction.

Do not address the user directly.

Do not praise the profile.

Do not mention uncertainty unless source information is
genuinely incomplete.

Do not mention:

- prompts;
- JSON;
- databases;
- language models;
- internal transformations;
- GetCurator implementation details.


============================================================
OUTPUT
============================================================

Return only the complete editorial profile.

Do not return JSON.

Do not use Markdown fences.

Do not include introductory text.

Do not include closing commentary.

Do not state that the profile was generated.

Do not ask a question.
""".strip()


# ============================================================
# HELPERS
# ============================================================

def _clean_optional_text(
    value: Optional[str],
) -> Optional[str]:

    if value is None:

        return None

    cleaned = value.strip()

    if not cleaned:

        return None

    return cleaned


def _clean_string_list(
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


def _clean_account_context(
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

        "name":
            _clean_optional_text(
                source.get(
                    "name"
                )
            ),

        "display_name":
            _clean_optional_text(
                source.get(
                    "display_name"
                )
            ),

        "company":
            _clean_optional_text(
                source.get(
                    "company"
                )
            ),

        "description":
            _clean_optional_text(
                source.get(
                    "description"
                )
            ),

        "profile_type":
            _clean_optional_text(
                source.get(
                    "profile_type"
                )
            ),

        "role":
            _clean_optional_text(
                source.get(
                    "role"
                )
            ),

    }


# ============================================================
# BUILD SOURCE PAYLOAD
# ============================================================

def build_profile_editorial_source_payload(
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
) -> Dict[str, Any]:

    cleaned_profile_text = (
        _clean_optional_text(
            profile_text
        )
    )

    if cleaned_profile_text is None:

        raise ValueError(
            "A validated profile_text is required "
            "to build an editorial profile."
        )

    supported_language = (
        language
        if language in {
            "fr",
            "en",
        }
        else "fr"
    )

    return {

        "output_language":
            supported_language,

        "validated_profile":
            cleaned_profile_text,

        "explicit_geographies":
            _clean_string_list(
                [
                    geography_1,
                    geography_2,
                    geography_3,
                ]
            ),

        "account_context":
            _clean_account_context(
                account_context
            ),

        "followed_items": {

            "companies":
                _clean_string_list(
                    companies
                ),

            "solutions":
                _clean_string_list(
                    solutions
                ),

            "topics":
                _clean_string_list(
                    topics
                ),

        },

    }


# ============================================================
# BUILD USER PROMPT
# ============================================================

def build_profile_editorial_user_prompt(
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

    return f"""
Transform the validated human-readable profile below into one
detailed internal editorial monitoring profile.

Preserve every useful relationship between:

- professional responsibilities;
- business priorities;
- actors and platforms;
- geographical markets;
- metrics and outcomes;
- current and future horizons;
- explicit exclusions.

Apply the USER or EXPERT path according to account_context.profile_type.
Expand the profile only through operational clarification.
Do not define questions, cadence or structure for a future report.

Do not invent missing business information.

Do not copy followed items whose role is unexplained.

Return only the complete editorial profile in the requested
output language.


============================================================
SOURCE PROFILE
============================================================

{json.dumps(
    source_payload,
    ensure_ascii=False,
    indent=2,
)}
""".strip()
