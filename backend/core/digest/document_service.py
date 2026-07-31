# backend/core/digest/document_service.py

from datetime import datetime
from typing import Literal

from core.delivery.models import (
    KnowledgeResult,
)

from core.digest.models import (
    DigestBadge,
    DigestCard,
    DigestDocument,
    DigestProfile,
    DigestSection,
)

from core.expertise.constants import (
    OUTPUT_SUMMARY,
    OUTPUT_IMPLICATIONS,
    OUTPUT_KEY_POINTS,
    OUTPUT_STRUCTURE,
    OUTPUT_OPPORTUNITIES,
    OUTPUT_RISKS,
    OUTPUT_BENCHMARK,
    OUTPUT_TIMELINE,
    OUTPUT_COMPARISON,
)

# ============================================================
# DISPLAY ORDER
# ============================================================

DISPLAY_ORDER = [

    OUTPUT_SUMMARY,

    OUTPUT_KEY_POINTS,

    OUTPUT_IMPLICATIONS,

    OUTPUT_STRUCTURE,

    OUTPUT_OPPORTUNITIES,

    OUTPUT_RISKS,

    OUTPUT_BENCHMARK,

    OUTPUT_TIMELINE,

    OUTPUT_COMPARISON,

]

# ============================================================
# SECTION TITLES
# ============================================================

SECTION_TITLES = {

    OUTPUT_SUMMARY:
        "Executive Summary",

    OUTPUT_KEY_POINTS:
        "Key Points",

    OUTPUT_IMPLICATIONS:
        "Strategic Implications",

    OUTPUT_STRUCTURE:
        "Market Structure",

    OUTPUT_OPPORTUNITIES:
        "Opportunities",

    OUTPUT_RISKS:
        "Risks",

    OUTPUT_BENCHMARK:
        "Benchmark",

    OUTPUT_TIMELINE:
        "Timeline",

    OUTPUT_COMPARISON:
        "Comparison",

}

SECTION_ARTICLES = "Articles"

# ============================================================
# BUILD DOCUMENT
# ============================================================

def build_digest_document(
    profile: DigestProfile,
    knowledge: KnowledgeResult,
    period_start: datetime,
    period_end: datetime,
    frequency: Literal["weekly", "monthly"],
    audience: Literal["user", "expert"],
) -> DigestDocument:
    """
    Build a DigestDocument from a KnowledgeResult.
    """

    sections: list[DigestSection] = []

    capability_results = (
        knowledge.capability_results
    )

    # ========================================================
    # CAPABILITIES
    # ========================================================

    for capability in DISPLAY_ORDER:

        result = capability_results.get(
            capability,
        )

        if not result:
            continue

        sections.append(

            DigestSection(

                title=SECTION_TITLES.get(
                    capability,
                    capability,
                ),

                content=result,

            )

        )

    # ========================================================
    # REMAINING CAPABILITIES
    # ========================================================

    for capability, result in capability_results.items():

        if capability in DISPLAY_ORDER:
            continue

        sections.append(

            DigestSection(

                title=capability.replace(
                    "_",
                    " ",
                ).title(),

                content=result,

            )

        )

    # ========================================================
    # ARTICLES
    # ========================================================

    cards = [

        _build_card(content)

        for content in knowledge.expertise.contents

    ]

    if cards:

        sections.append(

            DigestSection(

                title=SECTION_ARTICLES,

                content="",

                cards=cards,

            )

        )

    # ========================================================
    # DOCUMENT
    # ========================================================

    return DigestDocument(

        frequency=frequency,
        audience=audience,

        title=_build_title(
            period_start,
            period_end,
        ),

        subtitle="",

        period=_format_period(
            period_start,
            period_end,
        ),

        created_at=datetime.utcnow(),

        profile=profile,

        sections=sections,

    )

# ============================================================
# CARD
# ============================================================

def _build_card(
    content,
) -> DigestCard:

    return DigestCard(

        id=content.id,

        title=content.title,

        excerpt=content.excerpt,

        url=content.url,

        source_title=content.source_title,

        published_at=content.published_at,

    )


# ============================================================
# TITLE
# ============================================================

def _build_title(

    period_start: datetime,

    period_end: datetime,

) -> str:
    """
    Build the digest title.
    """

    duration = (
        period_end
        - period_start
    ).days

    if duration <= 8:

        return "Weekly Curator Digest"

    return "Monthly Curator Digest"


# ============================================================
# PERIOD
# ============================================================

def _format_period(

    period_start: datetime,

    period_end: datetime,

) -> str:
    """
    Format the digest period.
    """

    start = period_start.strftime(
        "%d %b %Y"
    )

    end = period_end.strftime(
        "%d %b %Y"
    )

    return f"{start} – {end}"
