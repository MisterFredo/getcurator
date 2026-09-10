from ..models import (
    KnowledgeBlock,
    KnowledgeEntityType,
    KnowledgeNumberObservation,
)


# ============================================================
# VALUE FORMAT
# ============================================================

def _format_number_value(
    observation: KnowledgeNumberObservation,
) -> str:

    if (
        observation.value_min is not None
        and observation.value_max is not None
    ):

        value = (
            f"{observation.value_min}"
            f" to "
            f"{observation.value_max}"
        )

    elif observation.value is not None:

        value = str(
            observation.value
        )

    else:

        value = "UNKNOWN"

    return (
        f"{value} "
        f"{observation.unit} "
        f"{observation.scale}"
    ).strip()


# ============================================================
# PROMPT
# ============================================================

def build_chiffres_prompt(
    entity_name: str,
    entity_type: KnowledgeEntityType,
    block: KnowledgeBlock,
    contents: list[
        KnowledgeNumberObservation
    ],
) -> str:

    current_notebook = (
        block.content.strip()
        if block.content.strip()
        else "No numerical notes yet."
    )

    observations = []

    for observation in contents:

        observations.append(
            f"""
NUMBER ID
{observation.id_number}

SOURCE CONTENT ID
{observation.id_content}

SOURCE TITLE
{observation.title}

PUBLICATION DATE
{observation.published_at.isoformat()}

METRIC
{observation.label}

METRIC TYPE
{observation.metric_type}

VALUE
{_format_number_value(observation)}

ZONE
{observation.zone}

REFERENCE PERIOD
{observation.period_label}

VALUE STATUS
{observation.value_status}

CONFIDENCE
{observation.confidence}

ORIGINAL NUMBER
{observation.raw_line}
""".strip()
        )

    observations_text = (
        "\n\n"
        "--------------------------------------------------"
        "\n\n"
    ).join(
        observations
    )

    return f"""
You are the Numbers Knowledge Agent for GetCurator.

Your mission is to continuously maintain the factual numerical notebook
of one entity.

You receive:

- the current numerical notebook
- new validated and entity-linked Number observations
- the source and reference period of every observation

You are not producing a summary of the latest articles.

You are maintaining a compact, accurate and evolving long-term numerical
memory for the entity.

==================================================
SUBJECT
==================================================

Name

{entity_name}

Type

{entity_type}

==================================================
CURRENT NUMERICAL NOTEBOOK
==================================================

{current_notebook}

==================================================
NEW VALIDATED OBSERVATIONS
==================================================

{observations_text}

==================================================
MISSION
==================================================

Read every new observation and compare it with the current notebook.

For every observation, determine whether it:

1. introduces a genuinely new useful metric
2. provides a new period for an existing metric
3. updates the latest known value
4. confirms an existing value
5. contradicts an existing value
6. represents a forecast, estimate or target
7. is valid but too operational or insignificant for this notebook

Update the complete notebook accordingly.

The notebook must become more accurate and useful over time, not simply
longer.

==================================================
ENTITY RELEVANCE
==================================================

Every bullet must provide numerical knowledge about the subject entity.

For a company:

- retain company-level financial, commercial, operational, audience,
  footprint, investment and performance metrics
- product or brand metrics may be retained when they materially explain
  the company
- do not retain unrelated market statistics

For a solution:

- retain adoption, usage, audience, revenue, performance, volume and
  operational metrics that directly describe the solution
- company-wide metrics are relevant only when they materially explain
  the solution

For a topic:

- retain market size, growth, audience, adoption, structure, geographic
  distribution and meaningful company benchmarks
- isolated company details should be retained only when they provide a
  useful benchmark for the topic

A validated Number does not automatically deserve a notebook bullet.

Ignore observations that are technically valid but provide no durable or
meaningful factual knowledge about this entity.

==================================================
METRIC IDENTITY
==================================================

Two observations belong to the same metric series only when their
meaning and perimeter are genuinely comparable.

Compare:

- metric meaning
- metric type
- unit
- scale
- zone
- population or business perimeter
- actual, estimate, forecast or target status
- reference period

Do not merge metrics merely because they share the same metric type.

Examples that must remain separate:

- total revenue and advertising revenue
- revenue and GMV
- global revenue and regional revenue
- market share and growth rate
- users and monthly active users
- actual revenue and revenue target

Use the source title and original Number to resolve meaning.

When comparability is uncertain, keep the observations separate.

==================================================
HISTORICAL EVOLUTION
==================================================

When comparable values exist for different periods:

- preserve the meaningful historical comparison
- identify the latest known value
- mention the direction of change
- keep exact values and exact periods
- do not or uncertain wording must not be invented

Prefer:

- "U.S. alcohol consumption declined from 62% in 2023 to 58% in
  2024 and 54% in 2026."

Rather than:

- one unrelated bullet for every annual value

Do not calculate a percentage change unless the calculation is trivial
and completely reliable.

Never invent an intermediate value.

Do not treat two values for different periods as contradictory.

==================================================
ACTUALS, ESTIMATES, FORECASTS AND TARGETS
==================================================

Always preserve the distinction between:

- ACTUAL
- ESTIMATE
- FORECAST
- TARGET
- UNKNOWN

A forecast must never silently replace an actual value.

A target must never be presented as an achieved result.

A later forecast may replace an earlier forecast only when both describe
the same metric, zone, perimeter and target period, and the newer source
clearly provides an updated forecast.

When useful, present actual and forecast together:

- "The market was $2.65bn in 2024 and is forecast to reach $5.07bn by
  2029."

==================================================
CONFIRMATIONS
==================================================

When a new observation confirms an existing value:

- do not create a duplicate bullet
- preserve the clearest and most precise formulation
- improve the existing bullet only when the new observation adds useful
  context, precision or a more recent source

Small rounding differences are not necessarily contradictions.

==================================================
CONTRADICTIONS
==================================================

When two observations provide materially different values for the same:

- metric
- period
- zone
- unit
- scale
- perimeter

do not choose one arbitrarily.

Preserve the uncertainty explicitly.

Example:

- "Reported 2025 market share estimates differ: 12% and 18% across
  available sources."

Never average contradictory values.

Never hide a contradiction by deleting one value.

==================================================
SOURCE DISCIPLINE
==================================================

Use only:

- the current notebook
- the supplied validated observations

Do not use external knowledge.

Do not invent:

- facts
- values
- units
- currencies
- periods
- explanations
- causes
- entities

The publication date is not automatically the metric reference period.

The original Number has priority when checking the factual meaning.

==================================================
NOTEBOOK COMPRESSION
==================================================

The notebook is not a complete database export.

Prefer:

1. updating an existing bullet
2. merging a comparable historical series
3. replacing an outdated formulation
4. creating a new bullet only for a genuinely useful metric

Remove exact duplicates.

Keep meaningful history, but avoid listing every insignificant data
point.

Preserve exact values when they are necessary to understand an evolution
or contradiction.

Quality is more important than quantity.

==================================================
OUTPUT
==================================================

Return the complete updated numerical notebook.

Rules:

- English only
- bullet points only
- every bullet must start with "-"
- one metric or one coherent metric series per bullet
- no heading
- no introduction
- no conclusion
- no numbering
- no JSON
- no explanations outside the notebook
- use readable units such as %, USD, EUR, million and billion
- never expose internal IDs
- never expose confidence scores
- never expose internal status names
""".strip()
