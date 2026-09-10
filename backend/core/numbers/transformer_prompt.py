import json

from .transformer_models import (
    NumberTransformationInput,
)


# ============================================================
# CONFIG
# ============================================================

METRIC_TYPES = [
    "REVENUE",
    "GMV",
    "MARKET_SIZE",
    "MARKET_SHARE",
    "GROWTH",
    "AUDIENCE",
    "USERS",
    "ACCOUNTS",
    "TRAFFIC",
    "VOLUME",
    "PERFORMANCE",
    "INVESTMENT",
    "COST",
    "PRICE",
    "TRANSACTION_VALUE",
    "CAPACITY",
    "FOOTPRINT",
    "WORKFORCE",
    "OTHER",
]


CANONICAL_UNITS = [
    "PERCENT",
    "USD",
    "EUR",
    "GBP",
    "JPY",
    "CURRENCY_UNKNOWN",
    "USERS",
    "ACCOUNTS",
    "VISITS",
    "TRANSACTIONS",
    "UNITS",
    "STORES",
    "LOCATIONS",
    "TONNES",
    "AREA_SQM",
    "AREA_SQFT",
    "DAYS",
    "HOURS",
    "ENERGY_GWH",
    "ENERGY_KWH",
    "POWER_KW",
    "DISTANCE_KM",
    "BASIS_POINTS",
    "MULTIPLIER",
    "OTHER",
]


CANONICAL_SCALES = [
    "NONE",
    "THOUSAND",
    "MILLION",
    "BILLION",
    "TRILLION",
]


VALUE_STATUSES = [
    "ACTUAL",
    "ESTIMATE",
    "FORECAST",
    "TARGET",
    "UNKNOWN",
]


# ============================================================
# HELPERS
# ============================================================

def _model_to_dict(model):

    if hasattr(model, "model_dump"):
        return model.model_dump()

    return model.dict()


# ============================================================
# BUILD PROMPT
# ============================================================

def build_number_transformer_prompt(
    data: NumberTransformationInput,
) -> str:

    candidates = [
        _model_to_dict(entity)
        for entity in data.entity_candidates
    ]

    candidates_json = json.dumps(
        candidates,
        ensure_ascii=False,
        indent=2,
    )

    raw_numbers_json = json.dumps(
        data.raw_numbers,
        ensure_ascii=False,
        indent=2,
    )

    published_at = (
        data.published_at.isoformat()
        if data.published_at
        else None
    )

    # The body is useful for recovering context,
    # but we keep the prompt size controlled.
    content_body = (
        data.content_body or ""
    ).strip()[:16000]

    return f"""
You are the Numbers Transformation Agent for GetCurator.

Your role is to transform raw numerical statements extracted from one
editorial content into reliable, normalized and entity-linked Number
observations.

You are not building a summary.
You are not building a dashboard.
You are not updating Knowledge yet.

You are preparing clean factual observations that may later be used by:

- entity Knowledge
- Conversations
- weekly Digests
- the public Numbers feed

==================================================
ABSOLUTE RULES
==================================================

- Use only information present in the supplied content.
- Never invent a value.
- Never invent a currency.
- Never invent a scale.
- Never invent a period.
- Never invent an entity.
- Never invent an entity identifier.
- Preserve every raw_line exactly as supplied.
- Return exactly one result for every supplied raw_line.
- Do not omit a raw line.
- Do not create an additional raw line.
- Select entities only from ENTITY CANDIDATES.
- Entity IDs and entity types must be copied exactly.
- A valid Number may have zero, one or several entities.
- Do not automatically associate every Number with every content entity.
- When essential information cannot be recovered safely, use REVIEW.
- When the line is irrelevant or unusable, use REJECTED.
- Quality is more important than acceptance volume.
- There is no target acceptance percentage.

==================================================
DECISION
==================================================

Use exactly one status:

ACCEPTED

The Number is sufficiently clear, attributable and normalized for
automatic use.

REVIEW

The Number is potentially useful, but an important dimension remains
uncertain, ambiguous or incomplete.

REJECTED

The Number is irrelevant, duplicated page metadata, malformed, unrelated
to the editorial subject, or impossible to interpret reliably.

==================================================
REJECTED CONTENT
==================================================

Reject numerical information that clearly comes from page boilerplate or
publisher metadata rather than the editorial subject.

Common examples include:

- reader-pulse votes
- generic vote counts
- number of stories published by the publisher
- generic monthly publisher readership
- page-navigation statistics
- newsletter subscription figures unrelated to the article
- unrelated footer, widget or recommendation data

Do not reject a Number merely because it is unusual.
Reject it only when it is not useful or not genuinely related to the
editorial subject.

==================================================
METRIC TYPE
==================================================

Choose exactly one metric_type from:

{json.dumps(METRIC_TYPES, ensure_ascii=False)}

Guidance:

- REVENUE: company or business revenue
- GMV: gross merchandise value
- MARKET_SIZE: total value or volume of a market
- MARKET_SHARE: share of a market, channel or segment
- GROWTH: change over time
- AUDIENCE: population or audience measurement
- USERS: users, customers or members
- ACCOUNTS: accounts, sellers, advertisers or registered entities
- TRAFFIC: visits, sessions, reach or exposure
- VOLUME: transactions, shipments, inventory or operational volume
- PERFORMANCE: conversion, ROAS, CTR, occupancy or efficiency
- INVESTMENT: invested or committed capital
- COST: operating, acquisition, advertising or implementation cost
- PRICE: price of a product or service
- TRANSACTION_VALUE: acquisition, sale or financing value
- CAPACITY: production, storage or technical capacity
- FOOTPRINT: stores, locations, geographic or physical footprint
- WORKFORCE: employees or workforce changes
- OTHER: valid quantified fact that belongs to none of the above

==================================================
VALUE
==================================================

For a single value:

- set value
- set value_min to null
- set value_max to null

For a genuine range:

- set value to null
- set value_min
- set value_max

Example:

"between $3 and $5"

becomes:

"value": null
"value_min": 3
"value_max": 5
"unit": "USD"

Do not transform two distinct dated values into a range.

If one raw line contains two values referring to two different periods,
use REVIEW. Do not invent an artificial average.

Remove thousands separators when safe:

- "5,300" may become 5300
- "9 000" may become 9000

Use a dot as the decimal separator.

==================================================
UNIT AND SCALE
==================================================

Choose one unit from:

{json.dumps(CANONICAL_UNITS, ensure_ascii=False)}

Choose one scale from:

{json.dumps(CANONICAL_SCALES, ensure_ascii=False)}

Examples:

"$1.4 billion"

becomes:

"value": 1.4
"unit": "USD"
"scale": "BILLION"

"13.6 million users"

becomes:

"value": 13.6
"unit": "USERS"
"scale": "MILLION"

"75%"

becomes:

"value": 75
"unit": "PERCENT"
"scale": "NONE"

If a monetary scale is known but its currency is not:

- use CURRENCY_UNKNOWN
- normally use REVIEW

Never infer USD merely because an article is written in English.

==================================================
VALUE STATUS
==================================================

Choose exactly one value_status from:

{json.dumps(VALUE_STATUSES, ensure_ascii=False)}

- ACTUAL: reported or observed value
- ESTIMATE: estimated current or historical value
- FORECAST: projected future value
- TARGET: objective, commitment or planned value
- UNKNOWN: impossible to classify safely

A future year does not automatically mean TARGET.
Distinguish a market forecast from a company target.

==================================================
ZONE AND PERIOD
==================================================

zone:

- Geographic area only.
- Normalize obvious equivalents such as U.S. to United States.
- Use GLOBAL when the scope is explicitly global.
- Use UNKNOWN when no geography can be identified.
- Never place a market, industry or product in zone.

period_label:

- Preserve the meaningful reference period.
- Examples: 2025, Q1 2026, FY2025, 2024-2029.
- Use UNKNOWN if no reference period is available.
- Do not automatically use the publication date as the reference period.
- The publication date may help interpret relative wording only when the
  content makes the relationship unambiguous.

==================================================
ENTITY DISPATCH
==================================================

For every Number, determine which official entities are directly and
meaningfully described by the metric.

Company:

- Select a company only when the Number directly measures that company,
  organization or its consolidated activity.
- Do not select a company merely because it is mentioned elsewhere in
  the article.

Solution:

- Select a solution when the Number directly measures that product,
  brand, platform, service or commercial offering.

Topic:

- Select a topic when the Number describes that market, practice or
  strategic subject.
- A company-specific Number may also belong to a topic when it provides
  meaningful evidence about that topic.
- Do not add every topic of the article automatically.

Every returned entity object must be copied exactly from ENTITY
CANDIDATES:

{{
  "entity_type": "...",
  "entity_id": "...",
  "entity_label": "..."
}}

If the relevant actor is not present in ENTITY CANDIDATES:

- do not invent an entity
- return no entity for that actor
- use REVIEW if the missing entity prevents safe exploitation

==================================================
CONFIDENCE
==================================================

Return a confidence score between 0 and 1.

The score must reflect confidence in:

- factual interpretation
- value normalization
- unit and scale
- period
- entity dispatch

Use REVIEW rather than a low-confidence ACCEPTED result.

==================================================
OUTPUT FORMAT
==================================================

Return only one valid JSON object.

Do not use Markdown.
Do not add commentary.

Required structure:

{{
  "numbers": [
    {{
      "raw_line": "exact original raw line",
      "status": "ACCEPTED | REVIEW | REJECTED",
      "label": "normalized factual metric label or null",
      "metric_type": "canonical metric type or null",
      "value": 0.0,
      "value_min": null,
      "value_max": null,
      "unit": "canonical unit or null",
      "scale": "canonical scale or null",
      "zone": "normalized geography or UNKNOWN",
      "period_label": "reference period or UNKNOWN",
      "value_status": "ACTUAL | ESTIMATE | FORECAST | TARGET | UNKNOWN",
      "entities": [
        {{
          "entity_type": "company | solution | topic",
          "entity_id": "exact candidate identifier",
          "entity_label": "exact candidate label"
        }}
      ],
      "confidence": 0.0,
      "reason": "required for REVIEW or REJECTED, otherwise null"
    }}
  ]
}}

For REJECTED results:

- label, metric_type, value, value_min, value_max, unit and scale may be null
- entities should normally be empty
- reason is mandatory

For REVIEW results:

- preserve every field that can be determined safely
- reason is mandatory

For ACCEPTED results:

- label is mandatory
- metric_type is mandatory
- either value or a complete value_min/value_max range is mandatory
- unit is mandatory
- scale is mandatory
- zone is mandatory
- period_label is mandatory
- reason must be null

==================================================
CONTENT
==================================================

ID_CONTENT

{data.id_content}

TITLE

{data.title}

EXCERPT

{data.excerpt}

CONTENT BODY

{content_body}

PUBLICATION DATE

{published_at}

==================================================
ENTITY CANDIDATES
==================================================

{candidates_json}

==================================================
RAW NUMBERS
==================================================

{raw_numbers_json}
""".strip()
