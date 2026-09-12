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

Your mission is to explain what the established developments
change for this specific professional.

The Key Points describe what changed.

Your response must explain why those changes matter for the
user's responsibilities, decisions, priorities and metrics.


============================================================
LANGUAGE
============================================================

Write the entire response in {output_language}.


============================================================
PROFESSIONAL PROFILE
============================================================

{profile_context}


============================================================
ESTABLISHED DEVELOPMENTS
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

Do not restate the Key Points.

Explain the concrete business consequences from the user's
professional perspective.

Focus only on consequences supported by the established
developments and supporting content.

Relevant consequences may concern:

- revenue or monetisation;
- costs and investment priorities;
- business models;
- distribution or market access;
- competitive positioning;
- customer or audience behaviour;
- operational responsibilities;
- measurement and performance;
- bargaining power;
- important metrics explicitly named in the profile.

Use a metric from the profile only when the connection is
credible and supported.

Do not force every profile priority or metric into the response.


============================================================
TASK
============================================================

1. Identify the two to four most important implications.
2. Rank them by importance for this professional.
3. Explain the specific business consequence.
4. State the responsibility, decision or metric affected when
   this is supported.
5. Combine developments only when they create the same
   consequence.
6. Omit weak or generic implications.


============================================================
OUTPUT FORMAT
============================================================

For each implication, use exactly:

A short standalone title of no more than 10 words.

One paragraph of no more than 55 words explaining:

- the concrete consequence for this user;
- the responsibility, decision, risk, opportunity or metric
  affected.

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

Be direct, precise and decision-oriented.

Use short sentences.

Address the reader directly when useful.

Prefer concrete formulations such as:

- This puts pressure on...
- This changes how you...
- This affects...
- This makes ... more difficult to measure.
- This increases the value of...
- This reduces...
- This creates a trade-off between...
- This may affect [explicit metric] through...

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
BOUNDARIES
============================================================

Do not introduce a new market development.

Do not summarise the articles.

Do not repeat the Key Points.

Do not mention article titles or publishers.

Do not mention the existence of a profile.

Do not invent a metric, objective, risk or opportunity.

Do not make a recommendation that is unsupported by the
evidence.

Do not produce one implication per article.

Every implication must add a distinct consequence.


============================================================
FINAL CHECK
============================================================

Before responding, verify that:

- every implication is specific to this professional;
- every implication follows from an established development;
- no implication merely restates what happened;
- no two implications make the same point;
- every paragraph contains a concrete consequence;
- no paragraph exceeds 55 words;
- the response contains no filler.

If only two implications are material, return two.
Never add an implication merely to reach a target.
""".strip()
