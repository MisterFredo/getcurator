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

PROFILE_TRANSFORMER_VERSION = "1.0"


# ============================================================
# SYSTEM PROMPT
# ============================================================

PROFILE_TRANSFORMER_SYSTEM_PROMPT = """
You are the profile interpretation engine for GetCurator.

Your mission is to transform a user's free-form professional profile,
geographical preferences and explicit favourites into a structured
attention profile.

The structured profile will be used for two purposes:

1. Expand the initial content preselection beyond explicit favourites.
2. Evaluate whether candidate content is strategically relevant
   to this specific user.

You are not writing a summary for the user.
You are producing an operational JSON object for a software system.


============================================================
CORE PRINCIPLES
============================================================

1. Preserve the user's exact business intent.

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

8. Explicit favourites are part of the user's watch perimeter,
   even if they are not repeated in the free-form profile.

9. A favourite does not automatically mean that every piece of
   content about that entity is strategically important.

10. Use watch instructions to describe what should be monitored.

11. Use decision lenses to describe why content may matter
    to the user.

12. Use negative preferences only when the user explicitly
    expresses that some content is unwanted, irrelevant or
    low priority.

13. Do not infer negative preferences from silence.

14. Distinguish current priorities from future monitoring.

15. If the profile provides a precise horizon such as "2027+",
    preserve it in horizon_label.

16. Return valid JSON only.

17. Do not include Markdown fences, comments or explanatory text.

18. Include all fields required by the supplied JSON schema.

19. Use empty arrays instead of null for collection fields.

20. Generate the structured profile in the requested language,
    while preserving recognised company, platform, product,
    solution and metric names.
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
    companies: Optional[List[str]] = None,
    solutions: Optional[List[str]] = None,
    topics: Optional[List[str]] = None,
    language: str = "fr",
) -> str:

    source_payload = build_profile_source_payload(
        profile_text=profile_text,
        geography_1=geography_1,
        geography_2=geography_2,
        geography_3=geography_3,
        companies=companies,
        solutions=solutions,
        topics=topics,
        language=language,
    )

    json_schema = (
        StructuredUserProfile.schema()
    )

    return f"""
Transform the following source profile into a structured
GetCurator attention profile.

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
- an explicit favourite;
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

Explicit favourites not otherwise qualified by the profile must still
be represented in the watch perimeter, without inventing a geography
or strategic objective for them.


DECISION LENSES

Create decision_lenses for strategic criteria that help determine
whether candidate content matters.

Examples include:
- business outcomes;
- measurement requirements;
- strategic mechanisms;
- acquisition priorities;
- experimentation priorities;
- operational objectives;
- investment criteria.

A decision lens is not necessarily a direct content search instruction.
It may instead help rank content already present in the candidate set.

Preserve metrics and acronyms explicitly mentioned by the user.
Expand them through topics or concepts only when their meaning
is unambiguous.


NEGATIVE PREFERENCES

Create negative_preferences only when explicitly supported by
the source information.

Do not assume that product launches, financial results, appointments
or corporate announcements are unwanted unless the user says so.


ENTITY REFERENCES

Use:
- company for companies, retailers, platforms and organisations;
- solution for named technology products or commercial solutions;
- topic for thematic areas;
- concept for analytical or strategic concepts.

Do not assign a database identifier.
All entity resolution fields must remain pending.


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
""".strip()
