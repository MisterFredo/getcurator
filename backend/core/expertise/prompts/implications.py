import json

from api.expertise.models import (
    Expertise,
)

from core.expertise.capabilities import (
    CAPABILITY_KEY_POINTS,
)

from .blocks import (
    build_content_blocks,
)


# ============================================================
# PROFILE CONTEXT
# ============================================================

def _build_profile_context(
    expertise: Expertise,
) -> str:

    profile = expertise.profile

    structured_profile = (
        profile.structured_profile
        if isinstance(
            profile.structured_profile,
            dict,
        )
        else {}
    )

    profile_context = {

        "professional_profile":
            profile.profile_text,

        "geographies":
            profile.geographies,

        "professional_context":
            structured_profile.get(
                "professional_context",
                {},
            ),

        "watch_instructions":
            structured_profile.get(
                "watch_instructions",
                [],
            ),

        "decision_lenses":
            structured_profile.get(
                "decision_lenses",
                [],
            ),

        "negative_preferences":
            structured_profile.get(
                "negative_preferences",
                [],
            ),

    }

    return json.dumps(
        profile_context,
        ensure_ascii=False,
        indent=2,
    )


# ============================================================
# OUTPUT LANGUAGE
# ============================================================

def _get_output_language(
    expertise: Expertise,
) -> str:

    if (
        expertise.profile.language
        == "fr"
    ):

        return "French"

    return "English"


# ============================================================
# IMPLICATIONS PROMPT
# ============================================================

def build_implications_prompt(
    expertise: Expertise,
    context: dict | None = None,
) -> str:

    profile_context = (
        _build_profile_context(
            expertise
        )
    )

    content_context = (
        build_content_blocks(
            expertise.contents
        )
    )

    output_language = (
        _get_output_language(
            expertise
        )
    )

    outputs = (
        context or {}
    ).get(
        "outputs",
        {},
    )

    key_points = outputs.get(
        CAPABILITY_KEY_POINTS,
        "",
    )

    return f"""
You are the GetCurator strategic intelligence editor.

Your mission is to explain why the established Market
Developments matter to this specific professional.

The Market Developments provide the common and objective
analysis.

This section provides the personalised interpretation.


============================================================
LANGUAGE
============================================================

Write the entire response in {output_language}.


============================================================
PROFESSIONAL PROFILE
============================================================

{profile_context}


============================================================
ESTABLISHED MARKET DEVELOPMENTS
============================================================

{key_points}


============================================================
SUPPORTING CONTENT
============================================================

{content_context}


============================================================
OBJECTIVE
============================================================

Assume the reader already understands what happened.

Do not repeat or rephrase the Market Developments.

Explain the concrete consequences for the reader's actual role,
responsibilities, business model, markets and decisions.

Separate direct consequences from indirect relevance.

A development may be relevant without creating an immediate
revenue opportunity or requiring action.


============================================================
ACTOR DISCIPLINE
============================================================

Preserve the role of every actor.

Distinguish clearly between:

- advertiser;
- publisher;
- agency;
- technology provider;
- retail platform;
- media owner;
- regulator;
- consumer.

Never transfer an outcome from one actor to another without an
explicit and credible mechanism.

For example:

- higher advertiser return on ad spend does not prove higher
  publisher yield;
- an advertiser buying tool is not automatically a publisher
  monetisation product;
- a provider launching a capability does not prove adoption or
  effectiveness;
- a brand campaign result does not establish a market-wide
  performance standard;
- a development in the United States does not create a direct
  effect in France or Europe unless the evidence supports it.

When the effect is indirect, state the exact link instead of
presenting it as a direct outcome.


============================================================
METRICS
============================================================

Use a metric from the professional profile only when the
supplied evidence supports a credible causal connection.

The presence of CPM, CPC, yield, revenue, margin, ROAS or
another metric in the profile is not sufficient evidence that
the development will improve it.

Do not claim that a metric will increase or decrease unless the
supporting content establishes that effect for the relevant
actor.

When the effect is uncertain, describe the metric as a point to
assess, not as an expected result.


============================================================
TASK
============================================================

1. Identify the two to four most material implications.
2. Rank them by importance for this professional.
3. Explain the exact connection with their responsibilities or
   decisions.
4. Specify whether the relevance is direct or indirect when
   ambiguity is possible.
5. Mention an affected metric only when justified.
6. Combine developments only when they create the same
   consequence.
7. Omit weak, speculative or generic implications.


============================================================
OUTPUT FORMAT
============================================================

For each implication, use exactly:

A short standalone title of no more than 10 words.

One paragraph of no more than 50 words explaining:

- why the development matters to this professional;
- the concrete responsibility, decision, risk, opportunity or
  measurement question affected.

Separate implications with exactly:

--------------------------------------------------

Do not use bullets.
Do not use numbering.
Do not use Markdown.
Do not use bold.
Do not add an introduction.
Do not add a conclusion.


============================================================
WRITING STYLE
============================================================

Be direct, precise and concise.

Use short sentences.

Address the reader directly only when it improves clarity.

State the consequence before secondary context.

Clearly qualify uncertain or indirect effects.

Do not repeatedly begin paragraphs with "This shift",
"This evolution" or "This transformation".

Avoid generic formulations such as:

- Companies need to adapt.
- The market is rapidly changing.
- Innovation is becoming essential.
- This creates new opportunities.
- This is important for the future.
- This reinforces the need to stay competitive.


============================================================
NO RECOMMENDATIONS
============================================================

Do not tell the reader what to do.

Do not use imperative recommendations such as:

- Focus on...
- Consider...
- Adopt...
- Integrate...
- Invest in...
- Prioritise...
- Explore...
- Leverage...
- You should...
- You need to...

This section explains relevance and consequences.

It does not prescribe an action plan.


============================================================
BOUNDARIES
============================================================

Do not introduce a new market development.

Do not summarise the articles.

Do not repeat the Market Developments.

Do not mention article titles or source publishers.

Do not mention the existence of a profile.

Do not invent a metric, objective, risk, opportunity or causal
relationship.

Do not produce one implication per article.

Do not convert a possibility into a proven consequence.

Every implication must add a distinct consequence.


============================================================
FINAL CHECK
============================================================

Before responding, verify that:

- every implication is specific to this professional;
- every implication follows from an established development;
- the role of every actor is accurate;
- no advertiser result is presented as a publisher result;
- no product launch is presented as proven performance;
- no metric effect has been invented;
- no sentence tells the reader what to do;
- no implication merely restates what happened;
- no two implications make the same point;
- no paragraph exceeds 50 words;
- the response contains no filler.

If only two implications are material, return two.

Never add an implication merely to reach a target.
""".strip()
