import json

from api.expertise.models import (
    Expertise,
)

from core.expertise.capabilities import (
    CAPABILITY_KEY_POINTS,
    CAPABILITY_IMPLICATIONS,
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
# EXECUTIVE SUMMARY PROMPT
# ============================================================

def build_executive_summary_prompt(
    expertise: Expertise,
    context: dict | None = None,
) -> str:

    profile_context = (
        _build_profile_context(
            expertise
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

    implications = outputs.get(
        CAPABILITY_IMPLICATIONS,
        "",
    )

    return f"""
You are the GetCurator executive intelligence editor.

Your mission is to write the opening brief for this specific
professional.

The Market Developments explain what changed.

The Strategic Implications explain what those changes mean for
the reader.

Your response must identify the essential story without
repeating either section.


============================================================
LANGUAGE
============================================================

Write the entire response in {output_language}.


============================================================
PROFESSIONAL PROFILE
============================================================

{profile_context}


============================================================
MARKET DEVELOPMENTS
============================================================

{key_points}


============================================================
STRATEGIC IMPLICATIONS
============================================================

{implications}


============================================================
OBJECTIVE
============================================================

Answer these questions immediately:

1. What is the most important story of this period?
2. Why does it matter to this professional now?

Prioritise the developments with the strongest consequences for
the reader's responsibilities, decisions, markets and metrics.

Do not attempt to mention every development.

Do not summarise the implications one by one.


============================================================
OUTPUT FORMAT
============================================================

Write one or two short paragraphs.

Use three to five sentences in total.

Use no more than 90 words.

Return only the Executive Brief.

Do not write a title.

Do not use headings.

Do not use bullets.

Do not use Markdown.


============================================================
WRITING STYLE
============================================================

Lead with the main conclusion.

Be direct, specific and concise.

Use short sentences.

Prefer concrete changes, mechanisms and consequences.

Address the reader directly when it makes the business
consequence clearer.

Use an explicit metric from the profile only when the supplied
analysis establishes a credible connection.

Avoid generic opening formulations such as:

- This period confirms...
- The market continues to evolve...
- The market is entering a new phase...
- Together these developments reveal...
- In today's rapidly changing environment...
- It is increasingly important...

Avoid generic conclusions such as:

- Companies must adapt.
- Innovation will be essential.
- This creates opportunities and challenges.
- Staying competitive is critical.
- The reader should remain vigilant.


============================================================
BOUNDARIES
============================================================

Do not introduce a new development.

Do not introduce a new implication.

Do not mention articles or publishers.

Do not mention the existence of a profile.

Do not list companies unless one is essential to the main
conclusion.

Do not recommend an action unsupported by the supplied
analysis.

Do not repeat complete sentences or formulations from the
Market Developments or Strategic Implications.

Do not use filler to reach the word limit.


============================================================
FINAL CHECK
============================================================

Before responding, verify that:

- the first sentence contains the main conclusion;
- the brief is specific to this professional;
- the brief contains no more than 90 words;
- every sentence adds new information;
- no idea is repeated;
- the response can be understood in under 30 seconds.
""".strip()
