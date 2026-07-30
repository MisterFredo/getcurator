# backend/core/digest/document_service.py

from datetime import datetime

from core.delivery.models import (
    KnowledgeResult,
)

from core.digest.models import (
    DigestCard,
    DigestDocument,
    DigestRequest,
    DigestSection,
)


# ============================================================
# BUILD DOCUMENT
# ============================================================

def build_digest_document(
    knowledge: KnowledgeResult,
    request: DigestRequest,
) -> DigestDocument:
    """
    Build the final DigestDocument from a KnowledgeResult.
    """

    sections: list[DigestSection] = []

    # ========================================================
    # EXECUTIVE SUMMARY
    # ========================================================

    if "summary" in knowledge.outputs:

        sections.append(
            DigestSection(
                title="Executive Summary",
                content=knowledge.outputs["summary"],
            )
        )

    # ========================================================
    # KEY POINTS
    # ========================================================

    if "key_points" in knowledge.outputs:

        sections.append(
            DigestSection(
                title="Key Points",
                content=knowledge.outputs["key_points"],
            )
        )

    # ========================================================
    # STRATEGIC IMPLICATIONS
    # ========================================================

    if "strategic_implications" in knowledge.outputs:

        sections.append(
            DigestSection(
                title="Strategic Implications",
                content=knowledge.outputs[
                    "strategic_implications"
                ],
            )
        )

    # ========================================================
    # ARTICLES
    # ========================================================

    sections.append(
        DigestSection(
            title="Articles",
            content="",
            cards=[
                _build_card(content)
                for content in knowledge.expertise.contents
            ],
        )
    )

    # ========================================================
    # DOCUMENT
    # ========================================================

    return DigestDocument(

        title="Weekly Curator Digest",

        subtitle="",

        period=_format_period(request),

        created_at=datetime.utcnow(),

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
# PERIOD
# ============================================================

def _format_period(
    request: DigestRequest,
) -> str:

    start = request.period_start.strftime(
        "%d %b %Y"
    )

    end = request.period_end.strftime(
        "%d %b %Y"
    )

    return f"{start} – {end}"
