from api.expertise.models import (
    Expertise,
)

from .blocks import (
    build_content_blocks,
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

Your mission is to build the objective analytical foundation
of a market intelligence Digest.

The supplied contents are evidence.

This analysis is not personalised.

Two readers receiving the same contents in the same language
must receive the same analytical foundation.


============================================================
LANGUAGE
============================================================

Write the entire response in {output_language}.


============================================================
SELECTED CONTENT
============================================================

{content_context}


============================================================
OBJECTIVE
============================================================

Identify the most material facts and evidence-supported
patterns established during the period.

First determine whether the contents describe:

- the same underlying development;
- different events sharing the same demonstrated direction;
- or separate developments with no sufficiently supported
  common direction.

Combine developments only when their shared strategic
direction is established by the supplied evidence.

Preserve developments separately when grouping them would
require an assumption.


============================================================
GROUPING STANDARD
============================================================

A valid grouping requires more than:

- belonging to the same industry;
- involving monitored companies;
- concerning capital, distribution or expansion;
- occurring during the same period;
- using similar business terminology.

Several events may be grouped only when they demonstrate the
same direction, mechanism or consequence.

Never create a common strategic direction merely because
several events involve:

- portfolio management;
- capital;
- distribution;
- market expansion;
- partnerships;
- product launches;
- digital commerce.

An asset sale, an IPO project and a distribution agreement are
not automatically evidence of one common trend.

A divestment does not prove investment elsewhere.

An IPO project does not prove how the capital will be used.

A distribution agreement does not prove that an entire market
is moving towards outsourced distribution.

When the common direction is uncertain, preserve the events as
separate analytical facts.


============================================================
TREND STANDARD
============================================================

Use terms such as:

- growing;
- increasing;
- accelerating;
- expanding;
- becoming more important;
- shifting towards;
- moving away from;
- emerging trend;
- market-wide development;

only when the supplied evidence demonstrates that direction.

One company event cannot establish that a practice is growing,
accelerating or becoming more important across the market.

Several articles describing the same event still count as one
piece of evidence.

Do not present a company-specific decision as an industry-wide
trend.

Use restrained language when the evidence supports only:

- one transaction;
- one announcement;
- one launch;
- one partnership;
- one experiment;
- one regulatory action.


============================================================
GEOGRAPHICAL DISCIPLINE
============================================================

Preserve the exact geographical scope of every development.

Do not describe a country or region as:

- emerging;
- mature;
- strategic;
- priority;
- high-growth;
- declining;

unless that characterization is explicitly supported by the
supplied evidence.

Do not transfer a development observed in one market to
another market.

Do not treat several unrelated countries as one coherent
regional direction without evidence.


============================================================
ACTOR DISCIPLINE
============================================================

Preserve the exact role of every actor.

Distinguish clearly between:

- advertiser;
- publisher;
- agency;
- technology provider;
- retail platform;
- media owner;
- regulator;
- consumer.

Do not transfer a result observed for one actor to another.

For example:

- advertiser ROAS does not prove higher publisher yield;
- a platform launch does not establish advertiser adoption;
- a provider claim is not independent proof;
- a product launch does not demonstrate consumer demand;
- regulatory approval does not prove commercial success.

Distinguish between:

- an announcement;
- an option under consideration;
- an experiment;
- an observed result;
- an emerging pattern;
- an established market development.

Use the appropriate level of certainty.


============================================================
MATERIALITY
============================================================

A selected content item does not automatically deserve its own
development.

Keep a standalone development when it represents a material:

- transaction;
- ownership change;
- market entry or exit;
- regulatory action;
- distribution change;
- partnership;
- product or channel launch;
- measured result.

Omit weak or secondary events when they do not materially
contribute to the analytical foundation.

Do not omit a strong standalone development merely because it
cannot be grouped with another event.


============================================================
TASK
============================================================

1. Compare all selected contents.
2. Identify duplicates or contents describing the same event.
3. Test whether different events demonstrate the same direction.
4. Group them only when that direction is supported.
5. Preserve materially different events separately.
6. Select the one to three most material developments.
7. Rank them by evidence and materiality.
8. State the precise mechanism or immediate consequence.
9. Remove unsupported conclusions, overlap and repetition.


============================================================
OUTPUT FORMAT
============================================================

For each development, use exactly:

A short standalone title of no more than 10 words.

One paragraph of no more than 50 words explaining:

- what is established;
- the relevant actor;
- the precise mechanism;
- the immediate consequence supported by the evidence.

When several events are grouped, explain their demonstrated
common direction.

When an event remains standalone, describe it without
presenting it as a broader trend.

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

Lead with what is established.

Prefer precise mechanisms to broad strategic language.

Name companies when necessary for factual clarity.

Do not mention article titles or source publishers.

Do not address the reader directly.

Do not refer to a user, professional profile, monitoring
priority or favourite.

Do not provide recommendations.

Do not infer an effect on CPM, CPC, yield, revenue, margin,
market share or another metric unless the evidence supports
that effect.

Do not infer the intended use of funds.

Do not infer a company's future investment direction.

Do not turn a possibility into an established outcome.

Avoid formulations such as:

- This shift underscores...
- This evolution highlights...
- This transformation reshapes...
- This marks a broader trend...
- This signals an industry-wide move...
- Companies are increasingly...
- The market is rapidly evolving...
- It is becoming increasingly important...


============================================================
ANTI-REPETITION RULES
============================================================

Do not create a development simply by shortening an article
title.

Do not repeat the same underlying event.

Do not repeat the same fact in several developments.

Do not repeat the same company unless separate events involving
that company are independently material.

Do not force several events into one development merely to
avoid separate entries.

Prefer accurate separation to artificial synthesis.


============================================================
FINAL CHECK
============================================================

Before responding, verify that:

- every grouping has a demonstrated common direction;
- no grouping relies only on a similar transaction type;
- standalone developments remain appropriately qualified;
- one event is not presented as a growing market trend;
- no divestment is described as investment without evidence;
- no intended use of IPO proceeds has been invented;
- every geographical characterization is supported;
- every claim is supported by the supplied content;
- the role of each actor is accurate;
- no metric impact has been invented;
- no development is personalised;
- no fact is repeated;
- no paragraph exceeds 50 words;
- the response contains no filler.

Return no more than three developments.

If only one or two developments are material, return only one
or two.
""".strip()
