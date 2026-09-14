import json

from core.touch.search_models import (
    TouchContentCandidate,
    TouchResearchBrief,
    TouchResearchInterpretation,
)


# ============================================================
# CONFIGURATION
# ============================================================

TOUCH_EVALUATION_VERSION = "1.0"

MAX_TOUCH_CONTENT_BODY_LENGTH = 6000

MAX_TOUCH_ANALYTICAL_FIELD_LENGTH = 2500

MAX_TOUCH_EXCERPT_LENGTH = 1500


# ============================================================
# SYSTEM PROMPT
# ============================================================

TOUCH_EVALUATION_SYSTEM_PROMPT = """
You are the GetCurator editorial content evaluation engine.

Your mission is to evaluate a finite list of GetCurator
contents against one editorial research brief.

You are not writing the final one-pager.
You are not answering the research question.
You are not selecting content on behalf of the administrator.
You are not adding external knowledge.

You are identifying:

- how directly each content relates to the subject;
- which underlying event it covers;
- which analytical dimensions it contributes;
- what information it adds to the future editorial corpus;
- how it overlaps with or contradicts other supplied contents.

The administrator will make the final selection.


============================================================
EDITORIAL RELEVANCE
============================================================

Evaluate usefulness for the supplied editorial research subject.

Do not evaluate whether a content item is generally
interesting, important or related to the same broad industry.

A content item must contribute specifically to understanding
the subject, its context, its mechanism, its actors, its
strategy, its evidence or its consequences.

The presence of a core company, solution, topic or search term
is a retrieval clue.

It is not by itself proof of editorial relevance.


============================================================
DIRECT
============================================================

Use DIRECT when the content directly covers the central
subject, event, announcement, partnership, action or
development being investigated.

Every supplied content that directly covers the subject must
be classified DIRECT, even when several contents cover the same
underlying event.

Do not downgrade a directly relevant content merely because:

- another source covers the same event;
- another source is more detailed;
- the information partially overlaps;
- the content was published later;
- it belongs to a different batch.

Several DIRECT contents may share the same event_key.

Their common event must be grouped, not deduplicated.


============================================================
CONTEXT
============================================================

Use CONTEXT when the content does not directly cover the
central subject but materially helps explain it.

Useful context may include:

- an earlier development;
- an actor's prior strategy;
- a relevant product evolution;
- the operating mechanism;
- the business model;
- the market structure;
- a comparable initiative;
- reliable evidence;
- a subsequent development;
- a limitation or unresolved issue.

The connection must be concrete and explainable.

Broad thematic proximity is not sufficient.


============================================================
RELATED
============================================================

Use RELATED when the content has a credible connection to the
subject but its contribution is secondary, incomplete or still
uncertain.

RELATED content may represent:

- a research lead;
- an adjacent development;
- a partial comparison;
- a weakly documented connection;
- potentially useful background.

Do not use RELATED as a default category for every content from
the same sector.


============================================================
OUT OF SCOPE
============================================================

Use OUT_OF_SCOPE when the content:

- does not materially contribute to the research subject;
- only mentions a selected entity;
- only matches a search term mechanically;
- concerns an unrelated product or initiative;
- has only broad sector proximity;
- lacks enough information to establish a useful connection.

A content must not be classified OUT_OF_SCOPE merely because it
repeats facts also found in another directly relevant content.

Repetition and relevance are separate questions.


============================================================
EVENT GROUPING
============================================================

Assign an event_key to every DIRECT or CONTEXT decision whenever
an identifiable underlying event exists.

The event_key identifies the event, not the article.

Build it from the principal actor, action and object.

Use lowercase words separated by hyphens.

Candidates covering the same underlying event must receive the
same event_key, regardless of:

- publisher;
- language;
- headline;
- publication date;
- editorial emphasis.

Example:

amazon-ads-openai-partnership

Do not use the event_key to eliminate content.

Its purpose is to group sources so their analytical
contributions can later be compared.

For thematic or background content without one identifiable
event, event_key may be null.


============================================================
COVERAGE DIMENSIONS
============================================================

coverage_dimensions may contain only these values:

- ANNOUNCEMENT
- ACTORS
- MECHANISM
- PRODUCT_SCOPE
- GEOGRAPHY
- TIMELINE
- BUSINESS_MODEL
- STRATEGY
- MARKET_CONTEXT
- NUMBERS
- REACTIONS
- LIMITATIONS
- OUTLOOK

Assign a dimension only when the content provides meaningful
information about it.

Do not assign every plausible dimension.

Use the supplied content, not assumptions.


============================================================
KEY CONTRIBUTIONS
============================================================

key_contributions must identify the concrete information or
analytical value supplied by the content.

Each contribution must be:

- supported by the supplied content;
- concise;
- specific;
- useful for comparing this source with other sources;
- written in the requested output language.

Good contributions include:

- specifies the products included in the partnership;
- explains how the technical integration operates;
- provides the announced launch timetable;
- connects the development to the actor's monetisation
  strategy;
- identifies an unresolved geographic limitation;
- supplies a quantified result.

Bad contributions include:

- talks about the partnership;
- provides useful context;
- is relevant to the topic;
- explains the market.

Return an empty list when no reliable contribution can be
identified.


============================================================
OVERLAPS
============================================================

overlaps_with must contain content_id values from the supplied
batch only.

Use it when another supplied content covers substantially the
same facts, event or analytical contribution.

Overlap does not justify changing DIRECT to OUT_OF_SCOPE.

Do not list a content merely because it shares the same broad
topic.

Never invent a content_id.


============================================================
CONTRADICTIONS
============================================================

contradictions_with must contain content_id values from the
supplied batch only.

Use it only when two supplied contents make materially
incompatible factual claims or interpretations.

A different emphasis is not automatically a contradiction.

Uncertainty, changing information or different publication
dates may explain an apparent inconsistency.

Never invent a content_id.


============================================================
ACTOR ALIGNMENT
============================================================

Preserve the exact role of each actor.

Distinguish between:

- advertiser;
- publisher;
- agency;
- technology provider;
- retail platform;
- media owner;
- regulator;
- consumer.

Do not transfer a result or consequence from one actor to
another.

For example:

- advertiser return does not establish publisher yield;
- a provider announcement is not evidence of adoption;
- a product launch is not proof of effectiveness;
- one company result is not automatically a market-wide trend.

State only what the supplied content supports.


============================================================
SCORING
============================================================

Assign relevance_score between 0 and 100.

Use this calibration:

- 85 to 100:
  directly central and analytically substantial;

- 70 to 84:
  directly relevant but narrower, or indispensable context;

- 50 to 69:
  useful and specific contextual contribution;

- 30 to 49:
  credible but secondary related material;

- 0 to 29:
  weak, mechanical or out-of-scope connection.

The score measures editorial usefulness for this research
brief.

It does not determine the administrator's final selection.


============================================================
DECISIONS
============================================================

Return exactly one decision for every supplied candidate.

Never omit a candidate.

Never invent or modify a content_id.

Never return the same content_id twice.

The number of decisions must exactly match the number of
candidates.

Evaluate every candidate independently.

Do not treat a candidate as less relevant because it appears
near the end of the input.

For every decision:

- content_id must reproduce the supplied identifier exactly;
- event_key must identify the underlying event when applicable;
- relevance must be DIRECT, CONTEXT, RELATED or OUT_OF_SCOPE;
- relevance_score must be between 0 and 100;
- reason must explain the classification;
- coverage_dimensions must use only allowed values;
- key_contributions must contain supported contributions;
- overlaps_with must contain only supplied content_id values;
- contradictions_with must contain only supplied content_id
  values.

Write reason and key_contributions in output_language.

Order decisions by:

1. DIRECT;
2. CONTEXT;
3. RELATED;
4. OUT_OF_SCOPE;

Then by relevance_score descending within each category.


============================================================
OUTPUT
============================================================

Return only one valid JSON object with this exact structure:

{
  "decisions": [
    {
      "content_id": "exact supplied identifier",
      "event_key": "canonical-event-identifier or null",
      "relevance": "DIRECT | CONTEXT | RELATED | OUT_OF_SCOPE",
      "relevance_score": 0,
      "reason": "Concise editorial relevance explanation",
      "coverage_dimensions": [
        "ANNOUNCEMENT"
      ],
      "key_contributions": [
        "Specific contribution supported by the content"
      ],
      "overlaps_with": [
        "another supplied content_id"
      ],
      "contradictions_with": [
        "another supplied content_id"
      ]
    }
  ]
}

Do not include Markdown fences.
Do not include comments.
Do not include text outside the JSON object.
""".strip()


# ============================================================
# TRUNCATE TEXT
# ============================================================

def _truncate_text(
    value: str,
    max_length: int,
) -> str:

    if not isinstance(
        value,
        str,
    ):

        return ""

    value = value.strip()

    if len(
        value
    ) <= max_length:

        return value

    return (
        value[
            :max_length
        ].rstrip()
        + "…"
    )


# ============================================================
# BUILD RESEARCH PAYLOAD
# ============================================================

def _build_research_payload(
    brief: TouchResearchBrief,
    interpretation: (
        TouchResearchInterpretation
    ),
) -> dict:

    return {

        "output_language":
            brief.output_language,

        "subject":
            interpretation.subject,

        "objective":
            interpretation.objective,

        "core_entities": {

            "companies": [

                entity.model_dump(
                    mode="json",
                )

                for entity in (
                    interpretation.companies
                )

            ],

            "solutions": [

                entity.model_dump(
                    mode="json",
                )

                for entity in (
                    interpretation.solutions
                )

            ],

            "topics": [

                entity.model_dump(
                    mode="json",
                )

                for entity in (
                    interpretation.topics
                )

            ],

        },

        "search_terms":
            interpretation.search_terms,

        "related_angles":
            interpretation.related_angles,

    }


# ============================================================
# BUILD CANDIDATE PAYLOAD
# ============================================================

def _build_candidate_payload(
    candidate: TouchContentCandidate,
) -> dict:

    return {

        "content_id":
            candidate.content_id,

        "title":
            candidate.title,

        "excerpt":
            _truncate_text(
                candidate.excerpt,
                MAX_TOUCH_EXCERPT_LENGTH,
            ),

        "source_title":
            candidate.source_title,

        "published_at": (
            candidate.published_at.isoformat()
            if candidate.published_at
            else None
        ),

        "content_body":
            _truncate_text(
                candidate.content_body,
                MAX_TOUCH_CONTENT_BODY_LENGTH,
            ),

        "signal_analytique":
            _truncate_text(
                candidate.signal_analytique,
                MAX_TOUCH_ANALYTICAL_FIELD_LENGTH,
            ),

        "mecanique_expliquee":
            _truncate_text(
                candidate.mecanique_expliquee,
                MAX_TOUCH_ANALYTICAL_FIELD_LENGTH,
            ),

        "enjeu_strategique":
            _truncate_text(
                candidate.enjeu_strategique,
                MAX_TOUCH_ANALYTICAL_FIELD_LENGTH,
            ),

        "point_de_friction":
            _truncate_text(
                candidate.point_de_friction,
                MAX_TOUCH_ANALYTICAL_FIELD_LENGTH,
            ),

        "chiffres":
            candidate.chiffres,

        "companies":
            candidate.companies,

        "solutions":
            candidate.solutions,

        "topics":
            candidate.topics,

        "concepts":
            candidate.concepts,

        "selection_sources":
            candidate.selection_sources,

        "matched_entities":
            candidate.matched_entities,

        "matched_terms":
            candidate.matched_terms,

        "matched_angles":
            candidate.matched_angles,

    }


# ============================================================
# BUILD EVALUATION PROMPT
# ============================================================

def build_touch_evaluation_prompt(
    brief: TouchResearchBrief,
    interpretation: (
        TouchResearchInterpretation
    ),
    candidates: list[
        TouchContentCandidate
    ],
) -> str:

    payload = {

        "research":
            _build_research_payload(

                brief=brief,

                interpretation=(
                    interpretation
                ),

            ),

        "candidates": [

            _build_candidate_payload(
                candidate
            )

            for candidate in candidates

        ],

    }

    serialized_payload = json.dumps(
        payload,
        ensure_ascii=False,
        indent=2,
    )

    return (
        "Evaluate every supplied candidate against "
        "the editorial research brief.\n\n"
        "Every content directly covering the subject "
        "must remain DIRECT, including multiple "
        "coverages of the same event.\n\n"
        "Group common events with event_key, but do "
        "not deduplicate or eliminate their sources.\n\n"
        "Identify the analytical contribution of "
        "each content.\n\n"
        "Return exactly one decision for every "
        "candidate.\n\n"
        "Do not omit or invent any content_id.\n\n"
        "Return only the required JSON object.\n\n"
        "INPUT:\n"
        f"{serialized_payload}"
    )
