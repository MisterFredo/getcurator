# backend/core/digest/render_service.py

from core.digest.models import (
    DigestReview,
    DigestDocument,
    DigestSection,
    DigestCard,
)


# ============================================================
# DISPLAY ORDER
# ============================================================

SECTION_ORDER = [

    "summary",

    "implications",

    "key_points",

    "structure",

    "opportunities",

    "risks",

    "benchmark",

    "timeline",

    "comparison",

]


# ============================================================
# RENDER DIGEST
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

    for capability in SECTION_ORDER:

        result = capability_results.get(
            capability,
        )

        if not result:
            continue

        sections.append(

            DigestSection(

                title=_format_title(
                    capability,
                ),

                body=result,

            )

        )

    # ========================================================
    # REMAINING CAPABILITIES
    # ========================================================

    for capability, result in (
        capability_results.items()
    ):

        if capability in SECTION_ORDER:
            continue

        sections.append(

            DigestSection(

                title=_format_title(
                    capability,
                ),

                body=result,

            )

        )

    # ========================================================
    # ARTICLES
    # ========================================================

    cards: list[DigestCard] = []

    for content in (
        review.knowledge.expertise.contents
    ):

        cards.append(

            DigestCard(

                title=content.title,

                excerpt=content.excerpt,

                url=content.url,

                company_logo=content.company_logo,

            )

        )

    sections.append(

        DigestSection(

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
    Convert an output capability into
    a readable section title.
    """

    return (
        capability
        .replace("_", " ")
        .title()
    )
