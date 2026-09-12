import json

from api.expertise.models import (
    Expertise,
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
# KEY POINTS PROMPT
# ============================================================

def build_key_points_prompt(
    expertise: Expertise,
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

    return f"""
You are the GetCurator market intelligence editor.

Your mission is to identify the few developments that matter
most to this specific professional during this period.

The supplied contents are evidence.
The professional profile determines the editorial angle.


============================================================
LANGUAGE
============================================================

Write the entire response in {output_language}.


============================================================
PROFESSIONAL PROFILE
============================================================

{profile_context}


============================================================
SELECTED CONTENT
============================================================

{content_context}


============================================================
OBJECTIVE
============================================================

Explain what materially changed within the user's monitoring
perimeter.

Do not summarise every article.

Do not attempt to use every supplied content item.

Combine contents only when they describe the same development.

Keep a standalone event when it materially changes the user's
operating environment, even if it is not yet a broad market
trend.

Select developments according to:

- the user's exact responsibilities;
- their strategic priorities;
- their relevant markets;
- their monitored business models;
- their important metrics and outcomes;
- the likely materiality of the development.

A thematic match alone is not sufficient.


============================================================
TASK
============================================================

1. Identify the two to four most important developments.
2. Rank them by relevance to this professional.
3. State what changed, not what an article said.
4. Include only information supported by the supplied content.
5. Remove overlapping or repetitive developments.
6. Omit weak developments rather than filling space.


============================================================
OUTPUT FORMAT
============================================================

For each development, use exactly:

A short standalone title of no more than 10 words.

One paragraph of no more than 45 words explaining:

- what changed;
- the concrete market or business consequence.

Separate developments with exactly:

--------------------------------------------------

Do not use bullets.
Do not use numbering.
Do not use Markdown.
Do not use bold.
Do not add an introduction.
Do not add a conclusion.


============================================================
WRITING RULES
============================================================

Be direct, factual and specific.

Use short sentences.

Lead with the change.

Prefer concrete mechanisms, consequences and measurable facts.

Use companies only when they are necessary to understand the
development.

Do not mention article titles or publishers.

Do not provide recommendations in this section.

Do not write generic statements about innovation, disruption,
competition or transformation.

Do not repeat the same idea using different words.

Avoid empty formulations such as:

- This shift underscores...
- This evolution highlights...
- This transformation reshapes...
- The market is rapidly evolving...
- Companies must adapt...
- It is increasingly important...

Every sentence must add a distinct piece of information.

If only two developments are materially supported, return two.
Never create an additional development merely to reach a target.


============================================================
FINAL CHECK
============================================================

Before responding, verify that:

- every development is relevant to the supplied profile;
- every development is supported by the supplied content;
- no two developments make the same point;
- no paragraph exceeds 45 words;
- the response contains no filler.
""".strip()
