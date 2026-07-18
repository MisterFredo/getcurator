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
    # CONTENTS
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

            title="Contents",

            body="",

            cards=cards,

        )

    )

    # ========================================================
    # DOCUMENT
    # ========================================================

    return DigestDocument(

        title="Curator Digest",

        period=(
            f"{review.request.period_start:%d/%m/%Y}"
            f" - "
            f"{review.request.period_end:%d/%m/%Y}"
        ),

        sections=sections,

    )


# ============================================================
# PRIVATE
# ============================================================

def _format_title(
    capability: str,
) -> str:

    return (
        capability
        .replace("_", " ")
        .title()
    )
