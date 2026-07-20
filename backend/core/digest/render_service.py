# backend/core/digest/render_service.py

from core.digest.models import (
    DigestReview,
    DigestDocument,
    DigestSection,
    DigestCard,
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

    OUTPUT_IMPLICATIONS,

    OUTPUT_KEY_POINTS,

    OUTPUT_STRUCTURE,

    OUTPUT_OPPORTUNITIES,

    OUTPUT_RISKS,

    OUTPUT_BENCHMARK,

    OUTPUT_TIMELINE,

    OUTPUT_COMPARISON,

]

ARTICLES_SECTION = "articles"


# ============================================================
# RENDER
# ============================================================

def render_digest(
    review: DigestReview,
) -> DigestDocument:
    """
    Convert a DigestReview into a DigestDocument.
    """

    sections: list[DigestSection] = []

    capability_results = (
        review.knowledge.capability_results
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
                id=capability,
                title=_format_title(capability),
                body=result,
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
                id=capability,
                title=_format_title(capability),
                body=result,
            )

        )

    # ========================================================
    # ARTICLES
    # ========================================================

    cards: list[DigestCard] = []

    for content in review.knowledge.expertise.contents:

        cards.append(

            DigestCard(
                id=content.id,
                title=content.title,
                excerpt=content.excerpt,
                url=content.url,
                source_title=content.source_title,
                published_at=content.published_at,
                company_logo=content.company_logo,
            )

        )

    if cards:

        sections.append(

            DigestSection(
                id="articles",
                title="Articles",
                body="",
                cards=cards,
            )

        )

    # ========================================================
    # DOCUMENT
    # ========================================================

    return DigestDocument(

        title=_build_title(
            review,
        ),

        period=(
            f"{review.request.period_start:%d/%m/%Y}"
            " - "
            f"{review.request.period_end:%d/%m/%Y}"
        ),

        sections=sections,

    )


# ============================================================
# PRIVATE
# ============================================================

def _build_title(
    review: DigestReview,
) -> str:
    """
    Build the document title.
    """

    duration = (
        review.request.period_end
        - review.request.period_start
    ).days

    if duration <= 8:

        return "Weekly Curator Digest"

    return "Monthly Curator Digest"


def _format_title(
    capability: str,
) -> str:
    """
    Convert a capability identifier into
    a readable section title.
    """

    return (
        capability
        .replace("_", " ")
        .title()
    )
