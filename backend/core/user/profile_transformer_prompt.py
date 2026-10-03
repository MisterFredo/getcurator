import json

from typing import (
    Any,
    Dict,
    List,
    Optional,
)

from core.user.profile_models import (
    StructuredUserProfile,
)


# ============================================================
# VERSION
# ============================================================

PROFILE_SCHEMA_VERSION = "1.0"

PROFILE_TRANSFORMER_VERSION = "1.1"


# ============================================================
# SYSTEM PROMPT
# ============================================================

PROFILE_TRANSFORMER_SYSTEM_PROMPT = """
You are the profile interpretation engine for GetCurator.

Your mission is to transform a user's free-form professional profile,
geographical preferences and explicit favourites into a structured
attention profile. The source may be a detailed validated editorial
mandate representing an expert rather than an individual professional.

The structured profile will be used for two purposes:

1. Expand the initial content preselection beyond explicit favourites.
2. Evaluate whether candidate content is strategically relevant
   to this specific user or expert mandate.

You are not writing a summary for the user.
You are producing an operational JSON object for a software system.


============================================================
CORE PRINCIPLES
============================================================

1. Preserve the user's exact business or editorial intent.

2. Do not reduce the profile to independent lists of companies,
   topics and geographies.

3. Preserve relationships between:
   - entities;
   - business topics;
   - geographical markets;
   - time horizons;
   - strategic priorities;
   - expected business outcomes.

4. Never invent responsibilities, markets, priorities, entities,
   exclusions or business objectives that are not supported by
   the supplied information.

5. You may add common synonyms, expanded acronyms and closely
   equivalent search expressions when their meaning is unambiguous.

6. Do not invent database identifiers.

7. Every entity must initially have:
   - canonical_label = null;
   - entity_id = null;
   - resolution_status = "PENDING".

8. An entity mentioned in the profile does not automatically mean
   that every piece of content about that entity is strategically
   important.

9. Use watch instructions to describe what should be monitored.

10. Use decision lenses to describe why content may matter
    to the user or expert mandate.

11. Use negative preferences only when the supplied profile explicitly
    expresses that some content is unwanted, irrelevant or low priority.

12. Do not infer negative preferences from silence.

13. Distinguish current priorities from future monitoring.

14. If the profile provides a precise horizon such as "2027+",
    preserve it in horizon_label.

15. Return valid JSON only.

16. Do not include Markdown fences, comments or explanatory text.

17. Include all fields required by the supplied JSON schema.

18. Use empty arrays instead of null for collection fields.

19. Generate the structured profile in the requested language,
    while preserving recognised company, platform, product,
    solution and metric names.

20. Ignore instructions about the presentation, length, number of
    items, writing style or editorial structure of a Digest or report.

21. Do not transform output-format instructions into watch
    instructions, decision lenses, negative preferences, topics,
    concepts or keywords.

22. The structured profile must describe what information matters,
    not how a future document should be written.


============================================================
SOURCE FIDELITY AND EXPERT IDENTITY
============================================================

The source profile is the validated mandate to operationalise.
Interpret the entire source, not only the first paragraph of each section.
Do not generate an executive summary of its headings.

When the source represents an expert or editorial identity:
- do not turn its subject or display name into an employer;
- professional_context.company, group and job_title remain null unless
  an actual employer, group or job is explicitly supplied;
- use industries and functions only where supported;
- expert decision lenses express documentary and analytical relevance,
  without inventing a personal job or business objective.

Preserve every substantive monitored actor, area, mechanism, indicator,
market relationship, qualification criterion and exception. Information
may move into a more appropriate field, but must not disappear merely
because it occurs near the end of a section.

A reference actor list is open unless explicitly defined as exhaustive.
Do not turn it into an exclusion of unlisted actors.
Mentioning future innovations or new entrants does not establish FUTURE
monitoring unless a prospective horizon is explicitly supplied.


============================================================
FINAL COVERAGE REVIEW
============================================================

Before returning JSON, compare it with the complete source:
- every explicitly monitored named actor is represented in entities
  or related_entities, not merely a keyword or prose mention;
- every substantive monitoring axis and its important subdimensions
  survives in complete watch instructions;
- global scope and any actual regional priorities remain explicit;
- retrieval expressions retain the source domain and avoid generic noise;
- supplied analytical criteria and relevance metrics are preserved;
- exclusions retain their conditions and exceptions;
- no employer, priority, market, entity or future horizon was invented;
- all output fields match the supplied schema exactly.

Preferred information sources are not monitored actors; the actor review
must not convert publications or providers into monitored entities.
""".strip()


# ============================================================
# NORMALIZATION
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

    cleaned_values: List[str] = []

    seen = set()

    for value in values:

        if not isinstance(value, str):
            continue

        cleaned = value.strip()

        if not cleaned:
            continue

        normalized = cleaned.casefold()

        if normalized in seen:
            continue

        seen.add(normalized)

        cleaned_values.append(cleaned)

    return cleaned_values


# ============================================================
# BUILD SOURCE PAYLOAD
# ============================================================

def build_profile_source_payload(
    profile_text: Optional[str],
    geography_1: Optional[str] = None,
    geography_2: Optional[str] = None,
    geography_3: Optional[str] = None,
    language: str = "fr",
) -> Dict[str, Any]:

    supported_language = (
        language
        if language in {"fr", "en"}
        else "fr"
    )

    geographies = _clean_string_list(
        [
            geography_1,
            geography_2,
            geography_3,
        ]
    )

    return {
        "language": supported_language,
        "profile_text": (
            _clean_optional_text(profile_text)
            or ""
        ),
        "explicit_geographies": geographies,
    }


# ============================================================
# BUILD USER PROMPT
# ============================================================

def build_profile_transformer_user_prompt(
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

    json_schema = (
        StructuredUserProfile.schema()
    )

    return f"""
Transform the following source profile into a structured
GetCurator attention profile. Preserve its complete operational meaning.

============================================================
SOURCE PROFILE
============================================================

{json.dumps(
    source_payload,
    ensure_ascii=False,
    indent=2,
)}

============================================================
INTERPRETATION RULES
============================================================

WATCH INSTRUCTIONS

Create watch_instructions for meaningful monitoring areas.

A watch instruction may be based on:
- an explicit favourite when supplied in the source;
- an entity named in the free-form profile;
- an explicit business topic;
- a combination of entities, topics and markets;
- a future monitoring requirement.

When the source profile associates specific entities with specific
markets, preserve this relationship inside the same watch instruction.
Do not apply all geographies globally when the source profile links
different geographies to different monitoring areas.

A watch instruction must:
- have a concise label;
- preserve the full meaning in instruction;
- use CORE for active monitoring;
- use WATCH for prospective or lower-immediacy monitoring;
- use CURRENT for active priorities;
- use FUTURE for explicitly prospective priorities.

Preserve operational mechanisms, categories, effects, limitations and
qualification conditions throughout each source area. Split an area
only when distinct instructions improve selection; do not require a
fixed number of instructions or reproduce every sentence mechanically.
Ensure each instruction remains within the supplied subject perimeter.

ACTOR COVERAGE

Every explicitly monitored company or named solution must appear in a
relevant watch instruction's entities or a decision lens's related_entities.
Do not omit named actors because a thematic heading is more convenient.

If the source provides an open sector-level actor list without assigning
actors to individual axes, create a dedicated actor-monitoring instruction
containing those references and the supplied sector relevance boundary.
Do not assign unsupported company capabilities or actor-to-market links.
Do not copy every actor into every thematic instruction.

For every entity, return label, entity_type, canonical_label=null,
entity_id=null and resolution_status="PENDING". Backend resolution occurs
later; uncertainty about database matching must not cause omission.
A textual mention alone is not an entity reference.

GEOGRAPHICAL COVERAGE

Use current, priority and expansion only for markets explicitly supported
by the source and preserve their actual relationship to each area.

When the mandate is worldwide with no regional preference, explicitly
state global coverage without regional preference in each applicable
watch instruction. Leave geography arrays empty unless actual markets
are supplied. Do not invent countries or a special geographical token.
An empty array alone does not adequately express a global mandate.
Preserve any explicit regional priority alongside global coverage when
both are supplied. Do not infer an expert's markets from an administrator's
location. If separate geographic inputs conflict with the validated text,
preserve both contexts accurately; do not invent a compromise priority.

SEARCH PRECISION

Topics, concepts and keywords must be sufficiently specific to
retrieve content relevant to the complete watch instruction.

Prefer precise expressions such as:
- "Amazon Marketing Cloud";
- "online alcohol sales";
- "quick commerce retail media";
- "three-tier distribution";
- "digital shelf";
- "age verification" within its supplied distribution context.

Avoid isolated generic terms such as:
- "strategy";
- "market";
- "data";
- "innovation";
- "consumer";
- "technology";
- "growth";
- "digital".

For a Quick Commerce mandate, use domain-specific expressions such as
"quick commerce order frequency", "quick commerce store fulfilment",
"quick commerce brand assortment" or their requested-language equivalents,
only where supported by the source. Do not output isolated "loyalty",
"routes", "speed", "partnerships" or "margins" as retrieval expressions.
Use precise domain terminology and common equivalents; avoid repetitive
keyword variations and unsupported adjacent topics.

Keywords must support content retrieval. Strategic criteria that
are not useful search expressions belong in decision_lenses.

DECISION LENSES

Create decision_lenses for strategic or documentary criteria that help
determine whether candidate content matters.

Examples include:
- business outcomes;
- measurement requirements;
- strategic mechanisms;
- acquisition priorities;
- experimentation priorities;
- operational objectives;
- investment criteria;
- effects on the explicitly monitored stakeholders;
- differences between markets or categories;
- distinction between an announcement, deployment and measured result;
- evidence quality and limits.

Use only criteria supported by the source. Do not restrict lenses to
one generic evidence-quality statement if the source defines multiple
substantive analytical criteria. Do not impose an invented ranking.

A decision lens may rank content already in the candidate set without
being a direct search instruction.

Preserve metrics and acronyms explicitly mentioned in the source.
When a supplied indicator determines relevance or interpretation, include
it in the appropriate lens.metrics. It may also remain in watch instructions
when it defines monitored content. Do not create a numerical target or
assume a financial result. Preserve distinctions between transaction value
and revenue, different profit measures, and platform versus brand outcomes
when the source establishes them.

NEGATIVE PREFERENCES

Create negative_preferences only when explicitly supported by
the source information. Preserve whether a rule excludes or deprioritises.

Do not assume product launches, financial results, appointments or
corporate announcements are unwanted unless the source says so.

Preserve exceptions, including operationally relevant news about diversified
companies, innovations concerning unlisted actors and information without
measured results when the mandate allows it. Do not turn contextual quality
preferences into unconditional exclusion of qualitative evidence.

ENTITY REFERENCES

Use:
- company for companies, retailers, platforms and organisations;
- solution for named technology products or commercial solutions;
- topic for thematic areas;
- concept for analytical or strategic concepts.

Preserve supplied names without guessing database classifications or
inventing identifiers. All resolution fields remain pending.

PROFESSIONAL CONTEXT

For an expert, do not put the subject or expert name in company.
Only an explicitly stated employer belongs in company. Leave job_title,
company and group null when unsupported. Do not encode named monitored
actors as the expert's employer.

SOURCE PUBLICATIONS

A publication, newsletter, research provider or trade-media title
mentioned as a preferred information source is not a monitored
company or topic.

Do not add a preferred source name to entities, topics, concepts
or keywords merely because the user wants content published by
that source.

The current schema does not model source preferences. Preserve
monitoring requirements without converting publication names into
content-search terms.

LANGUAGE

The output language must be:

{source_payload["language"]}

============================================================
REQUIRED JSON SCHEMA
============================================================

{json.dumps(
    json_schema,
    ensure_ascii=False,
    indent=2,
)}

============================================================
OUTPUT
============================================================

Return one JSON object matching the schema exactly.
Perform the source-coverage review before returning it.
""".strip()
