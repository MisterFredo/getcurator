# backend/core/digest/render_service.py

from core.digest.models import (
    DigestReview,
    DigestDocument,
    DigestSection,
    DigestCard,
)


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

    # ========================================================
    # CAPABILITIES
    # ========================================================

    for capability, result in (
        review.knowledge.capability_results.items()
    ):

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

    for content in review.knowledge.expertise.contents:

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

    return "Curator Digest"


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
