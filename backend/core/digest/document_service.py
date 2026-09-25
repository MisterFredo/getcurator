from datetime import (
    datetime,
    timezone,
)

from typing import (
    Any,
    Literal,
)

from api.expertise.models import (
    ExpertiseContent,
)

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

from core.expertise.capabilities import (
    CAPABILITY_EXECUTIVE_SUMMARY,
    CAPABILITY_KEY_POINTS,
    CAPABILITY_IMPLICATIONS,
    CAPABILITY_STRUCTURE,
)


# ============================================================
# CONFIGURATION
# ============================================================

DIGEST_TITLE = (
    "Weekly Curator Digest"
)


# ============================================================
# DISPLAY ORDER
# ============================================================

DISPLAY_ORDER = [

    CAPABILITY_EXECUTIVE_SUMMARY,

    CAPABILITY_KEY_POINTS,

    CAPABILITY_IMPLICATIONS,

    CAPABILITY_STRUCTURE,

]


# ============================================================
# SECTION TITLES
# ============================================================

SECTION_TITLES = {

    CAPABILITY_EXECUTIVE_SUMMARY:
        "Executive Summary",

    CAPABILITY_KEY_POINTS:
        "Key Points",

    CAPABILITY_IMPLICATIONS:
        "Strategic Implications",

    CAPABILITY_STRUCTURE:
        "Market Structure",

}


SECTION_SELECTED_CONTENTS = (
    "Selected for You"
)


# ============================================================
# BUILD DOCUMENT
# ============================================================

def build_digest_document(
    profile: DigestProfile,
    knowledge: KnowledgeResult,
    period_start: datetime,
    period_end: datetime,
    audience: Literal[
        "user",
        "expert",
    ],
    additional_contents: list[
        ExpertiseContent
    ] | None = None,
) -> DigestDocument:
    """
    Build one DigestDocument from a KnowledgeResult.

    Main sections and selected cards are built exclusively from
    the contents included in the KnowledgeResult expertise.

    Additional contents remain outside the analytical foundation
    and are exposed separately for lightweight rendering.
    """

    sections: list[DigestSection] = []

    capability_results = (
        knowledge.capability_results
    )

    additional_contents = (
        additional_contents
        or []
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

    for capability, result in (
        capability_results.items()
    ):

        if capability in DISPLAY_ORDER:

            continue

        if not result:

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
    # SELECTION DECISIONS
    # ========================================================

    selection_decisions = (
        _get_selection_decisions(
            knowledge
        )
    )

    # ========================================================
    # SELECTED ARTICLES
    # ========================================================

    selected_cards: list[
        DigestCard
    ] = []

    for content in (
        knowledge.expertise.contents
    ):

        decision = (
            selection_decisions.get(
                content.id
            )
        )

        selected_cards.append(

            _build_card(

                content=content,

                decision=decision,

            )

        )

    if selected_cards:

        sections.append(

            DigestSection(

                title=SECTION_SELECTED_CONTENTS,

                content="",

                cards=selected_cards,

            )

        )

    # ========================================================
    # ADDITIONAL CONTENTS
    # ========================================================

    additional_cards: list[
        DigestCard
    ] = []

    for content in additional_contents:

        decision = (
            selection_decisions.get(
                content.id
            )
        )

        # Additional contents must originate from
        # an ADJACENT selection decision.
        if (
            not isinstance(
                decision,
                dict,
            )
            or decision.get(
                "relevance_class"
            )
            != "ADJACENT"
        ):

            continue

        additional_cards.append(

            _build_card(

                content=content,

                decision=decision,

            )

        )

    # ========================================================
    # DOCUMENT
    # ========================================================

    return DigestDocument(

        audience=audience,

        title=DIGEST_TITLE,

        subtitle="",

        period=_format_period(

            period_start,

            period_end,

        ),

        created_at=datetime.now(
            timezone.utc,
        ),

        profile=profile,

        sections=sections,

        additional_contents=(
            additional_cards
        ),

    )


# ============================================================
# GET SELECTION DECISIONS
# ============================================================

def _get_selection_decisions(
    knowledge: KnowledgeResult,
) -> dict[str, dict[str, Any]]:

    metadata = (
        knowledge.metadata
        if isinstance(
            knowledge.metadata,
            dict,
        )
        else {}
    )

    selection = (
        metadata.get(
            "digest_selection"
        )
        or {}
    )

    if not isinstance(
        selection,
        dict,
    ):

        return {}

    decisions = (
        selection.get(
            "decisions"
        )
        or []
    )

    decisions_by_id = {}

    for decision in decisions:

        if not isinstance(
            decision,
            dict,
        ):

            continue

        content_id = decision.get(
            "content_id"
        )

        if not content_id:

            continue

        decisions_by_id[
            content_id
        ] = decision

    return decisions_by_id


# ============================================================
# NORMALIZE STRING LIST
# ============================================================

def _normalize_string_list(
    value: Any,
) -> list[str]:

    if not isinstance(
        value,
        list,
    ):

        return []

    return [

        str(
            item
        )

        for item in value

        if item

    ]


# ============================================================
# BUILD CARD
# ============================================================

def _build_card(
    content: ExpertiseContent,
    decision: dict[
        str,
        Any,
    ] | None = None,
) -> DigestCard:

    badges: list[DigestBadge] = []

    decision = (
        decision
        if isinstance(
            decision,
            dict,
        )
        else {}
    )

    # ========================================================
    # COMPANIES
    # ========================================================

    for company in content.companies:

        if not isinstance(
            company,
            dict,
        ):

            continue

        label = company.get(
            "name"
        )

        if not label:

            continue

        badges.append(

            DigestBadge(

                label=label,

                type="company",

            )

        )

    # ========================================================
    # TOPICS
    # ========================================================

    for topic in content.topics:

        if not isinstance(
            topic,
            dict,
        ):

            continue

        label = topic.get(
            "label"
        )

        if not label:

            continue

        badges.append(

            DigestBadge(

                label=label,

                type="topic",

            )

        )

    # ========================================================
    # SOLUTIONS
    # ========================================================

    for solution in content.solutions:

        if not isinstance(
            solution,
            dict,
        ):

            continue

        label = solution.get(
            "name"
        )

        if not label:

            continue

        badges.append(

            DigestBadge(

                label=label,

                type="solution",

            )

        )

    # ========================================================
    # CARD
    # ========================================================

    return DigestCard(

        id=content.id,

        title=content.title,

        excerpt=content.excerpt,

        url=content.url,

        source_title=(
            content.source_title
        ),

        published_at=(
            content.published_at
        ),

        badges=badges,

        selection_priority=(
            decision.get(
                "priority"
            )
        ),

        selection_relevance_class=(
            decision.get(
                "relevance_class"
            )
        ),

        selection_score=(
            decision.get(
                "relevance_score"
            )
        ),

        selection_reason=(
            decision.get(
                "reason"
            )
        ),

        matched_priorities=(
            _normalize_string_list(

                decision.get(
                    "matched_priorities"
                )

            )
        ),

        matched_negative_preferences=(
            _normalize_string_list(

                decision.get(
                    "matched_negative_preferences"
                )

            )
        ),

    )


# ============================================================
# PERIOD
# ============================================================

def _format_period(
    period_start: datetime,
    period_end: datetime,
) -> str:
    """
    Format the Digest weekly period.
    """

    start = period_start.strftime(
        "%d %b %Y"
    )

    end = period_end.strftime(
        "%d %b %Y"
    )

    return f"{start} – {end}"
