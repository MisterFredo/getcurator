import json

from core.touch.search_models import (
    TouchCandidateEvaluationResult,
    TouchContentCandidate,
    TouchResearchBrief,
    TouchResearchInterpretation,
)


# ============================================================
# CONFIGURATION
# ============================================================

TOUCH_CONSOLIDATION_VERSION = "1.1"


# ============================================================
# SYSTEM PROMPT
# ============================================================

TOUCH_CONSOLIDATION_SYSTEM_PROMPT = """
You are the GetCurator editorial corpus consolidation engine.

Your mission is to compare the evaluated content candidates
produced during an editorial research session.

You are not writing the one-pager.
You are not answering the research question.
You are not selecting content on behalf of the administrator.
You are not adding external knowledge.

You are consolidating the analytical findings already
extracted from the supplied GetCurator contents.


============================================================
CORE OBJECTIVE
============================================================

Build a global view of the proposed editorial material.

Identify:

- which contents cover the same underlying event;
- what information they share;
- how their contributions complement one another;
- whether they contain material contradictions;
- which analytical dimensions are already covered;
- which dimensions remain insufficiently documented;
- which follow-up searches could improve the corpus.

The purpose is to help the administrator decide which contents
to retain and what to investigate next.


============================================================
SOURCE PRESERVATION
============================================================

Do not eliminate sources.

Do not select one article as the only valid coverage of an
event.

Several contents covering the same event may all be useful.

Group them under one event_key and explain how their analytical
contributions differ or complement one another.

Repetition must be identified, but it must not be treated as
proof that a content is irrelevant.


============================================================
EVENT KEY HARMONISATION
============================================================

The individual evaluation was performed in several batches.

Similar events may therefore have received slightly different
event_key values.

Harmonise event keys globally.

Contents concern the same event when they describe the same:

- principal actor or actors;
- action;
- announcement;
- partnership;
- transaction;
- product launch;
- legal case;
- study;
- measurable business development.

Create one canonical event_key for each identifiable event.

Build it from the principal actor, action and object.

Use lowercase words separated by hyphens.

Example:

amazon-ads-openai-partnership

Do not merge different events merely because they involve the
same company or broad topic.


============================================================
EVENT GROUPS
============================================================

Create an event group when one or more supplied contents
describe an identifiable event.

Each group must include:

- one canonical event_key;
- one concise factual label;
- all relevant supplied content_id values;
- the principal information shared by the sources;
- their complementary analytical contributions;
- any material contradictions.

A group may contain one content when no other supplied source
covers the same event.

Do not invent a content_id.

Do not include OUT_OF_SCOPE content in an event group.


============================================================
SHARED INFORMATION
============================================================

shared_information identifies facts or analytical elements
reported by several contents in the same event group.

Include an item only when it is supported by at least two
supplied contents.

Do not infer consensus from one source.

Do not use vague formulations such as:

- the articles discuss the partnership;
- the sources cover the same topic;
- the contents provide information.

Return an empty list when the group contains only one content
or no meaningful shared element can be established.


============================================================
COMPLEMENTARY CONTRIBUTIONS
============================================================

complementary_contributions explains how the contents complete
one another.

Identify contributions such as:

- one source provides the announcement details;
- another explains the mechanism;
- another supplies quantified evidence;
- another places the event in a strategic sequence;
- another identifies a limitation;
- another provides a subsequent development.

Mention the relevant content_id when this helps the
administrator understand the contribution.

Do not invent information absent from the supplied individual
evaluations.


============================================================
CONTRADICTIONS
============================================================

Report only material contradictions supported by the supplied
evaluations.

A different editorial emphasis is not a contradiction.

A missing detail is not a contradiction.

Different publication dates may explain an apparent
inconsistency.

When uncertainty remains, describe it as an unresolved
difference rather than asserting that one source is wrong.

============================================================
RESEARCH AXIS COVERAGE
============================================================

The research brief may contain several distinct research axes.

Assess every supplied research axis separately.

For every research axis, return exactly one axis_coverage item.

Use the supplied axis_id, axis_type and label exactly.

For each axis:

- identify the non-OUT_OF_SCOPE contents that materially
  document it;
- assess whether the axis is COVERED, PARTIAL or MISSING;
- explain what the corpus establishes for that axis;
- identify any remaining documentary gaps.

Use COVERED when the corpus contains sufficient concrete
information to document the axis meaningfully.

Use PARTIAL when the corpus contains relevant information but
important parts of the axis remain insufficiently documented.

Use MISSING when no retained content materially documents the
axis.

MISSING axis coverage must have an empty content_ids list.

COVERED and PARTIAL axis coverage must reference at least one
non-OUT_OF_SCOPE content_id.

One content may contribute to several research axes.

Do not confuse retrieval clues with evidence.

A selected company or matched search term does not establish
that an axis is covered.


============================================================
CROSS-CONTEXT READINESS
============================================================

When research_type is CROSS_CONTEXT_ANALYSIS, the corpus must
document both:

- the source or core-subject side;
- the target-context side.

Set ready_for_notebook to false when:

- the core-subject axis is MISSING;
- the target-context axis is MISSING;
- the corpus contains only broad thematic proximity for one
  side;
- the available evidence cannot support a meaningful
  cross-context documentary reading.

Set ready_for_notebook to true when both sides contain at least
PARTIAL documentary coverage.

ready_for_notebook is a corpus-quality signal for the
administrator.

It does not authorize unsupported recommendations or invented
comparisons.


============================================================
COVERAGE ANALYSIS
============================================================

Assess the corpus against the stated research objective.

covered_dimensions may contain only:

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

Mark a dimension as covered only when the supplied evaluations
contain meaningful information about it.

Do not mark a dimension as covered merely because one content
mentions it superficially.


============================================================
MISSING DIMENSIONS
============================================================

missing_dimensions must contain only dimensions that would be
materially useful for this specific research objective.

Do not automatically list every dimension that is not covered.

For example, GEOGRAPHY may be irrelevant to some research
questions, while BUSINESS_MODEL or MECHANISM may be essential.

gaps must explain precisely what information is missing or
insufficient.

Do not invent the missing answer.


============================================================
STRENGTHS
============================================================

strengths must explain what the current proposed corpus
documents particularly well.

Base every strength on the supplied evaluations.

Do not use generic praise.


============================================================
FOLLOW-UP SEARCHES
============================================================

suggested_follow_ups must contain concise research requests the
administrator could submit next.

Each suggestion must:

- address an identified gap;
- remain connected to the current subject;
- be usable as a follow-up search request;
- avoid assuming an unsupported fact.

Good example:

Find content explaining Amazon Ads' strategic interest in the
OpenAI partnership.

Bad example:

Research more about artificial intelligence.


============================================================
OUTPUT LANGUAGE
============================================================

Write:

- event labels;
- shared information;
- complementary contributions;
- contradictions;
- summary;
- strengths;
- gaps;
- suggested follow-ups;

in output_language.

Keep event_key values in canonical lowercase English-style
identifiers.


============================================================
OUTPUT
============================================================

Return only one valid JSON object with this exact structure:

{
  "event_groups": [
    {
      "event_key": "canonical-event-identifier",
      "label": "Concise factual event label",
      "content_ids": [
        "exact supplied content_id"
      ],
      "shared_information": [
        "Information supported by several sources"
      ],
      "complementary_contributions": [
        "Distinct contribution supplied by one or more sources"
      ],
      "contradictions": [
        "Material contradiction or unresolved difference"
      ]
    }
  ],
  "coverage_analysis": {
    "summary": "Concise assessment of the proposed corpus",
    "axis_coverage": [
      {
        "axis_id": "exact supplied axis_id",
        "axis_type": "exact supplied axis_type",
        "label": "exact supplied axis label",
        "status": "COVERED | PARTIAL | MISSING",
        "content_ids": [
          "exact supplied content_id"
        ],
        "summary": "Concise assessment of this research axis",
        "gaps": [
          "Specific information missing for this axis"
        ]
      }
    ],
    "ready_for_notebook": true,
        "covered_dimensions": [
          "ANNOUNCEMENT"
    ],
    "missing_dimensions": [
      "BUSINESS_MODEL"
    ],
    "strengths": [
      "Specific strength of the current corpus"
    ],
    "gaps": [
      "Specific information still missing"
    ],
    "contradictions": [
      "Material contradiction across the corpus"
    ],
    "suggested_follow_ups": [
      "Precise follow-up research request"
    ]
  }
}

Do not include Markdown fences.
Do not include comments.
Do not include text outside the JSON object.
""".strip()


# ============================================================
# BUILD CANDIDATE INDEX
# ============================================================

def _build_candidate_index(
    candidates: list[
        TouchContentCandidate
    ],
) -> dict[
    str,
    TouchContentCandidate
]:

    return {

        candidate.content_id:
            candidate

        for candidate in candidates

    }


# ============================================================
# BUILD CONSOLIDATION ITEMS
# ============================================================

def _build_consolidation_items(
    candidates: list[
        TouchContentCandidate
    ],
    evaluation: (
        TouchCandidateEvaluationResult
    ),
) -> list[dict]:

    candidates_by_id = (
        _build_candidate_index(
            candidates
        )
    )

    items = []

    for decision in evaluation.decisions:

        candidate = candidates_by_id.get(
            decision.content_id
        )

        if candidate is None:

            continue

        items.append({

            "content_id":
                decision.content_id,

            "title":
                candidate.title,

            "source_title":
                candidate.source_title,

            "published_at": (
                candidate.published_at.isoformat()
                if candidate.published_at
                else None
            ),

            "relevance":
                decision.relevance,

            "relevance_score":
                decision.relevance_score,

            "event_key":
                decision.event_key,

            "reason":
                decision.reason,

            "coverage_dimensions":
                decision.coverage_dimensions,

            "key_contributions":
                decision.key_contributions,

            "overlaps_with":
                decision.overlaps_with,

            "contradictions_with":
                decision.contradictions_with,

        })

    return items


# ============================================================
# BUILD CONSOLIDATION PROMPT
# ============================================================

def build_touch_consolidation_prompt(
    brief: TouchResearchBrief,
    interpretation: (
        TouchResearchInterpretation
    ),
    candidates: list[
        TouchContentCandidate
    ],
    evaluation: (
        TouchCandidateEvaluationResult
    ),
) -> str:

    payload = {

        "output_language":
            brief.output_language,

        "research": {

            "original_query":
                brief.query,
        
            "subject":
                interpretation.subject,
        
            "central_question":
                interpretation.central_question,
        
            "objective":
                interpretation.objective,
        
            "research_type":
                interpretation.research_type,
        
            "scope_summary":
                interpretation.scope_summary,
        
            "target_context":
                interpretation.target_context,
        
            "organization_mode":
                interpretation.organization_mode,
        
            "time_granularity":
                interpretation.time_granularity,
        
            "geographies":
                interpretation.geographies,
        
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

            "research_axes": [
        
                axis.model_dump(
                    mode="json",
                )
        
                for axis in (
                    interpretation.axes
                )
        
            ],
        
            "search_terms":
                interpretation.search_terms,
        
            "related_angles":
                interpretation.related_angles,
        
            "assumptions":
                interpretation.assumptions,
        
            "editorial_cautions":
                interpretation.editorial_cautions,
        
            "missing_information":
                interpretation.missing_information,
        
        },

            "search_terms":
                interpretation.search_terms,

            "related_angles":
                interpretation.related_angles,

        },

        "evaluated_contents":
            _build_consolidation_items(

                candidates=candidates,

                evaluation=evaluation,

            ),

    }

    serialized_payload = json.dumps(
        payload,
        ensure_ascii=False,
        indent=2,
    )

    return (
        "Consolidate the supplied content evaluations "
        "against the editorial research objective.\n\n"
        "Assess every supplied research axis separately "
        "and return exactly one axis_coverage item for "
        "each axis.\n\n"
        "For cross-context research, verify that both "
        "the core-subject side and the target-context "
        "side are documented.\n\n"
        "Harmonise event groups across all evaluation "
        "batches.\n\n"
        "Do not eliminate sources that cover the same "
        "event.\n\n"
        "Explain how their analytical contributions "
        "overlap or complement one another.\n\n"
        "Identify what the proposed corpus covers and "
        "what still needs to be researched.\n\n"
        "Do not add external knowledge.\n\n"
        "Return only the required JSON object.\n\n"
        "INPUT:\n"
        f"{serialized_payload}"
    )
