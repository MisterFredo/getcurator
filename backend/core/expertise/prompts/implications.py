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

Your mission is to explain the most important consequences of
the analytical foundation for this specific professional.

The analytical foundation explains what changed.

Your response must explain what those changes alter in the
professional's operating environment.

It must not repeat the developments in personalised language.


============================================================
LANGUAGE
============================================================

Write the entire response in {output_language}.


============================================================
PROFESSIONAL PROFILE
============================================================

{profile_context}


============================================================
ANALYTICAL FOUNDATION
============================================================

{key_points}


============================================================
SUPPORTING CONTENT
============================================================

{content_context}


============================================================
OBJECTIVE
============================================================

Identify the one or two consequences that matter most for the
reader's responsibilities, decisions, markets or measurement
framework.

Look first for consequences shared by several developments.

A strong implication should explain a broader consequence such
as:

- a change in capital allocation;
- a change in market access;
- a change in distribution strategy;
- a change in competitive positioning;
- a change in operating models;
- a change in consumer acquisition;
- a change in measurement reliability;
- a change in bargaining power;
- a change in investment exposure.

Use these categories only when supported by the evidence.

Do not produce one implication for every development.


============================================================
TRANSVERSAL SYNTHESIS
============================================================

Compare all developments before writing.

Determine whether several developments create the same
consequence for the reader.

When they do, combine them into one implication.

For example:

- an asset disposal and an IPO project may jointly affect how
  the reader interprets capital allocation towards growth
  markets;
- several distribution partnerships may jointly indicate
  greater reliance on local operating capabilities;
- several social-commerce initiatives may jointly affect
  consumer recruitment and channel experimentation.

Do not force unrelated developments into one implication.

When developments are genuinely unrelated, retain only the one
or two consequences most material to the profile.

Omit secondary implications instead of repeating every event.


============================================================
PROFILE USE
============================================================

Use the profile to prioritise consequences.

Consider:

- exact responsibilities;
- strategic priorities;
- monitored business models;
- relevant markets;
- decision criteria;
- expected outcomes;
- explicitly named metrics;
- negative preferences.

The profile determines which consequences matter most.

It must not be quoted or described in the response.

Address the reader using only "you" and "your" when direct
reference improves clarity.

Never mention the reader's name, employer, title or the
existence of a profile.


============================================================
ACTOR DISCIPLINE
============================================================

Preserve the exact role of every actor.

Distinguish between:

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

- advertiser ROAS does not prove higher publisher yield;
- an advertiser buying tool is not automatically a publisher
  monetisation product;
- a product launch does not prove adoption or effectiveness;
- one campaign result does not establish a market-wide
  performance standard;
- a development in one country does not create a direct effect
  in another country without supporting evidence.

When relevance is indirect, state the connection precisely.


============================================================
METRICS
============================================================

Mention a profile metric only when the evidence establishes a
credible connection for the relevant actor.

Do not claim that CPM, CPC, yield, revenue, margin, ROAS,
market share or another metric will improve or decline unless
the evidence supports that effect.

When the effect is uncertain, describe:

- a measurement question;
- a decision variable;
- an exposure;
- a constraint;
- an element whose impact remains to be established.

Do not convert uncertainty into an expected result.


============================================================
TASK
============================================================

1. Compare every development with the professional profile.
2. Identify shared consequences across developments.
3. Select no more than two material implications.
4. Rank them by importance for the reader.
5. Explain the consequence before its supporting context.
6. State whether the connection is indirect when necessary.
7. Mention a metric only when justified.
8. Remove repetition, weak implications and generic commentary.


============================================================
OUTPUT FORMAT
============================================================

For each implication, use exactly:

A short standalone title of no more than 8 words.

One paragraph of no more than 45 words explaining:

- the transversal consequence;
- the responsibility, decision, exposure or measurement
  question affected;
- the direct or indirect connection when clarification is
  necessary.

Separate two implications with exactly:

--------------------------------------------------

Do not use bullets.

Do not use numbering.

Do not use Markdown.

Do not use bold.

Do not add an introduction.

Do not add a conclusion.


============================================================
TITLE RULES
============================================================

Write titles around strategic consequences, not events.

Do not copy or paraphrase a Market Development title.

Do not use a company name in a title.

Do not create titles such as:

- Diageo's African Strategy
- Pernod Ricard's Indian IPO
- Rémy Cointreau's Distribution Change
- Sephora's TikTok Strategy
- Amazon's Regulatory Challenges

Prefer consequence-oriented titles such as:

- Capital Allocation Moves Toward Growth Markets
- Local Partnerships Gain Strategic Weight
- Social Commerce Expands Consumer Recruitment
- Measurement Reliability Becomes More Critical

Use these examples only when supported by the evidence.


============================================================
ANTI-REPETITION RULES
============================================================

Do not produce one implication per Market Development.

Do not reproduce the sequence of the analytical foundation.

Do not begin an implication by summarising one event.

Do not restate what a company announced, launched, sold,
acquired or partnered on.

Do not explain again what happened.

Explain only what the combined evidence changes for the
reader.

Do not repeat the same company, fact or mechanism in several
implications.

Prefer one strong transversal implication to two repetitive
ones.


============================================================
NO RECOMMENDATIONS
============================================================

Explain consequences without prescribing a response.

Do not tell the reader what to do.

Do not formulate an implication as an instruction, obligation
or call to action.

Do not use formulations such as:

- You should...
- You must...
- You need to...
- You may need to...
- You have to...
- Consider...
- Focus on...
- Prioritise...
- Explore...
- Adopt...
- Integrate...
- Invest in...
- Leverage...
- This highlights the need to...
- This suggests a need to...
- This requires you to...
- Cela vous incite à...
- Vous devriez...
- Vous devez...
- Il vous faut...
- Il est nécessaire de...

Describe the decision or measurement question affected without
recommending a response.


============================================================
WRITING STYLE
============================================================

Be direct, precise and concise.

Use short sentences.

Lead with the strategic consequence.

Use restrained analytical language.

Clearly qualify indirect or uncertain effects.

Avoid generic formulations such as:

- This is strategically important.
- This creates opportunities and challenges.
- The market is rapidly changing.
- Innovation is becoming essential.
- Companies need to adapt.
- This reinforces the need to remain competitive.
- Cela souligne l'importance de...
- Cela met en lumière la nécessité de...


============================================================
FINAL CHECK
============================================================

Before responding, verify that:

- no more than two implications are returned;
- each implication describes a consequence, not an event;
- related developments have been consolidated;
- no implication corresponds mechanically to one article;
- no title contains a company name;
- no title repeats a Market Development;
- every implication is specific to the professional;
- the reader's name, employer and title do not appear;
- the role of every actor is accurate;
- no unsupported metric effect has been introduced;
- no sentence recommends an action;
- no two implications make the same point;
- no paragraph exceeds 45 words;
- the response contains no filler.

If only one transversal implication is material, return one.

Never create a second implication merely to reach a target.
""".strip()
