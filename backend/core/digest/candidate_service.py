from dataclasses import (
    dataclass,
    field,
)

from typing import (
    Any,
    Optional,
)

from api.expertise.models import (
    ExpertiseContent,
    ExpertisePreferences,
    ExpertiseProfile,
)

from core.digest.selection_models import (
    DigestContentCandidate,
)

from core.expertise.profile_service import (
    load_profile,
)

from core.expertise.selection_engine import (
    select_contents,
)


# ============================================================
# CONFIGURATION
# ============================================================

DEFAULT_CANDIDATE_LIMIT_PER_SOURCE = 40

DEFAULT_TOTAL_CANDIDATE_LIMIT = 60


# ============================================================
# INTERNAL CONTEXT
# ============================================================

@dataclass
class DigestCandidateContext:

    favorite_company_ids: set[str] = field(
        default_factory=set,
    )

    favorite_solution_ids: set[str] = field(
        default_factory=set,
    )

    favorite_topic_ids: set[str] = field(
        default_factory=set,
    )

    profile_company_ids: set[str] = field(
        default_factory=set,
    )

    profile_solution_ids: set[str] = field(
        default_factory=set,
    )

    profile_topic_ids: set[str] = field(
        default_factory=set,
    )

    profile_terms: set[str] = field(
        default_factory=set,
    )

    entity_watch_labels: dict[
        tuple[str, str],
        set[str],
    ] = field(
        default_factory=dict,
    )

    term_watch_labels: dict[
        str,
        set[str],
    ] = field(
        default_factory=dict,
    )


# ============================================================
# CLEAN TEXT
# ============================================================

def _clean_text(
    value: Any,
) -> str:

    if not isinstance(
        value,
        str,
    ):

        return ""

    return value.strip()


# ============================================================
# NORMALIZE TEXT
# ============================================================

def _normalize_text(
    value: Any,
) -> str:

    return (
        _clean_text(
            value
        )
        .casefold()
    )


# ============================================================
# ADD ENTITY WATCH LABEL
# ============================================================

def _add_entity_watch_label(
    context: DigestCandidateContext,
    entity_type: str,
    entity_id: str,
    watch_label: str,
) -> None:

    key = (
        entity_type,
        entity_id,
    )

    if key not in context.entity_watch_labels:

        context.entity_watch_labels[
            key
        ] = set()

    if watch_label:

        context.entity_watch_labels[
            key
        ].add(
            watch_label
        )


# ============================================================
# ADD PROFILE TERM
# ============================================================

def _add_profile_term(
    context: DigestCandidateContext,
    term: Any,
    watch_label: str,
) -> None:

    cleaned_term = _clean_text(
        term
    )

    if not cleaned_term:

        return

    normalized_term = (
        cleaned_term.casefold()
    )

    context.profile_terms.add(
        cleaned_term
    )

    if (
        normalized_term
        not in context.term_watch_labels
    ):

        context.term_watch_labels[
            normalized_term
        ] = set()

    if watch_label:

        context.term_watch_labels[
            normalized_term
        ].add(
            watch_label
        )


# ============================================================
# BUILD CANDIDATE CONTEXT
# ============================================================

def build_digest_candidate_context(
    profile: ExpertiseProfile,
) -> DigestCandidateContext:

    context = DigestCandidateContext(

        favorite_company_ids=set(
            profile.preferences.companies
        ),

        favorite_solution_ids=set(
            profile.preferences.solutions
        ),

        favorite_topic_ids=set(
            profile.preferences.topics
        ),

    )

    structured_profile = (
        profile.structured_profile
        if isinstance(
            profile.structured_profile,
            dict,
        )
        else {}
    )

    watch_instructions = (
        structured_profile.get(
            "watch_instructions"
        )
        or []
    )

    for watch in watch_instructions:

        if not isinstance(
            watch,
            dict,
        ):

            continue

        watch_label = (
            _clean_text(
                watch.get(
                    "label"
                )
            )
            or _clean_text(
                watch.get(
                    "instruction"
                )
            )
        )

        entities = (
            watch.get(
                "entities"
            )
            or []
        )

        for entity in entities:

            if not isinstance(
                entity,
                dict,
            ):

                continue

            entity_type = _clean_text(
                entity.get(
                    "entity_type"
                )
            )

            entity_id = _clean_text(
                entity.get(
                    "entity_id"
                )
            )

            entity_label = (
                _clean_text(
                    entity.get(
                        "canonical_label"
                    )
                )
                or _clean_text(
                    entity.get(
                        "label"
                    )
                )
            )

            if (
                entity_type == "company"
                and entity_id
            ):

                context.profile_company_ids.add(
                    entity_id
                )

                _add_entity_watch_label(
                    context=context,
                    entity_type="company",
                    entity_id=entity_id,
                    watch_label=watch_label,
                )

                continue

            if (
                entity_type == "solution"
                and entity_id
            ):

                context.profile_solution_ids.add(
                    entity_id
                )

                _add_entity_watch_label(
                    context=context,
                    entity_type="solution",
                    entity_id=entity_id,
                    watch_label=watch_label,
                )

                continue

            if (
                entity_type == "topic"
                and entity_id
            ):

                context.profile_topic_ids.add(
                    entity_id
                )

                _add_entity_watch_label(
                    context=context,
                    entity_type="topic",
                    entity_id=entity_id,
                    watch_label=watch_label,
                )

                continue

            if entity_label:

                _add_profile_term(
                    context=context,
                    term=entity_label,
                    watch_label=watch_label,
                )

        for field_name in (
            "topics",
            "concepts",
            "keywords",
        ):

            values = (
                watch.get(
                    field_name
                )
                or []
            )

            for value in values:

                _add_profile_term(
                    context=context,
                    term=value,
                    watch_label=watch_label,
                )

    return context


# ============================================================
# BUILD FAVORITES PROFILE
# ============================================================

def _build_favorites_profile(
    profile: ExpertiseProfile,
) -> ExpertiseProfile:

    return profile.model_copy(

        update={

            "keywords": [],

            "structured_profile":
                profile.structured_profile,

        },

    )


# ============================================================
# BUILD PROFILE EXPANSION PROFILE
# ============================================================

def _build_profile_expansion_profile(
    profile: ExpertiseProfile,
    context: DigestCandidateContext,
) -> Optional[ExpertiseProfile]:

    preferences = ExpertisePreferences(

        companies=list(
            context.profile_company_ids
        ),

        solutions=list(
            context.profile_solution_ids
        ),

        topics=list(
            context.profile_topic_ids
        ),

    )

    keywords = sorted(
        context.profile_terms
    )

    if not (
        preferences.companies
        or preferences.solutions
        or preferences.topics
        or keywords
    ):

        return None

    return profile.model_copy(

        update={

            "preferences":
                preferences,

            "keywords":
                keywords,

            "structured_profile":
                profile.structured_profile,

        },

    )


# ============================================================
# ENTITY IDS
# ============================================================

def _get_entity_ids(
    values: list[dict],
    id_field: str,
) -> set[str]:

    return {

        value.get(
            id_field
        )

        for value in values

        if (
            isinstance(
                value,
                dict,
            )
            and value.get(
                id_field
            )
        )

    }


# ============================================================
# ENTITY LABEL
# ============================================================

def _get_entity_label(
    value: dict,
) -> str:

    for key in (
        "name",
        "label",
        "canonical_label",
        "title",
    ):

        label = _clean_text(
            value.get(
                key
            )
        )

        if label:

            return label

    return ""


# ============================================================
# MATCHED FAVORITE LABELS
# ============================================================

def _get_matched_favorite_labels(
    content: ExpertiseContent,
    context: DigestCandidateContext,
) -> list[str]:

    labels = []

    entity_groups = (

        (
            content.companies,
            "id_company",
            context.favorite_company_ids,
        ),

        (
            content.solutions,
            "id_solution",
            context.favorite_solution_ids,
        ),

        (
            content.topics,
            "id_topic",
            context.favorite_topic_ids,
        ),

    )

    for (
        values,
        id_field,
        favorite_ids,
    ) in entity_groups:

        for value in values:

            if not isinstance(
                value,
                dict,
            ):

                continue

            if (
                value.get(
                    id_field
                )
                not in favorite_ids
            ):

                continue

            label = _get_entity_label(
                value
            )

            if (
                label
                and label not in labels
            ):

                labels.append(
                    label
                )

    return labels


# ============================================================
# SEARCHABLE CONTENT TEXT
# ============================================================

def _build_searchable_content_text(
    content: ExpertiseContent,
) -> str:

    values = [

        content.title,

        content.excerpt,

        content.content_body,

        content.signal,

        content.mecanique,

        content.enjeu,

        content.friction,

    ]

    return " ".join(
        _normalize_text(
            value
        )
        for value in values
        if value
    )


# ============================================================
# MATCH PROFILE
# ============================================================

def _match_profile(
    content: ExpertiseContent,
    context: DigestCandidateContext,
) -> tuple[
    list[str],
    list[str],
]:

    watch_labels: set[str] = set()

    matched_terms: set[str] = set()

    entity_groups = (

        (
            content.companies,
            "id_company",
            "company",
        ),

        (
            content.solutions,
            "id_solution",
            "solution",
        ),

        (
            content.topics,
            "id_topic",
            "topic",
        ),

    )

    for (
        values,
        id_field,
        entity_type,
    ) in entity_groups:

        entity_ids = _get_entity_ids(
            values,
            id_field,
        )

        for entity_id in entity_ids:

            labels = (
                context.entity_watch_labels.get(
                    (
                        entity_type,
                        entity_id,
                    ),
                    set(),
                )
            )

            watch_labels.update(
                labels
            )

    searchable_text = (
        _build_searchable_content_text(
            content
        )
    )

    for term in context.profile_terms:

        normalized_term = (
            term.casefold()
        )

        if (
            normalized_term
            not in searchable_text
        ):

            continue

        matched_terms.add(
            term
        )

        watch_labels.update(
            context.term_watch_labels.get(
                normalized_term,
                set(),
            )
        )

    return (
        sorted(
            watch_labels
        ),
        sorted(
            matched_terms
        ),
    )


# ============================================================
# BUILD CANDIDATE
# ============================================================

def _build_candidate(
    content: ExpertiseContent,
    context: DigestCandidateContext,
) -> DigestContentCandidate:

    selection_sources = []

    company_ids = _get_entity_ids(
        content.companies,
        "id_company",
    )

    solution_ids = _get_entity_ids(
        content.solutions,
        "id_solution",
    )

    topic_ids = _get_entity_ids(
        content.topics,
        "id_topic",
    )

    if (
        company_ids
        & context.favorite_company_ids
    ):

        selection_sources.append(
            "FAVORITE_COMPANY"
        )

    if (
        solution_ids
        & context.favorite_solution_ids
    ):

        selection_sources.append(
            "FAVORITE_SOLUTION"
        )

    if (
        topic_ids
        & context.favorite_topic_ids
    ):

        selection_sources.append(
            "FAVORITE_TOPIC"
        )

    profile_entity_match = bool(

        (
            company_ids
            & context.profile_company_ids
        )

        or (
            solution_ids
            & context.profile_solution_ids
        )

        or (
            topic_ids
            & context.profile_topic_ids
        )

    )

    (
        matched_watch_instructions,
        matched_profile_terms,
    ) = _match_profile(
        content=content,
        context=context,
    )

    if profile_entity_match:

        selection_sources.append(
            "PROFILE_ENTITY"
        )

    if matched_profile_terms:

        selection_sources.append(
            "PROFILE_TERM"
        )

    return DigestContentCandidate(

        content_id=content.id,

        title=content.title,

        excerpt=content.excerpt,

        source_title=content.source_title,

        published_at=content.published_at,

        selection_sources=(
            selection_sources
        ),

        matched_favorites=(
            _get_matched_favorite_labels(
                content=content,
                context=context,
            )
        ),

        matched_watch_instructions=(
            matched_watch_instructions
        ),

        matched_profile_terms=(
            matched_profile_terms
        ),

    )


# ============================================================
# MERGE CONTENT POOLS
# ============================================================

def _merge_content_pools(
    pools: list[list[ExpertiseContent]],
    limit: int,
) -> list[ExpertiseContent]:

    merged = []

    seen_ids = set()

    position = 0

    while len(merged) < limit:

        found_content = False

        for pool in pools:

            if position >= len(pool):

                continue

            found_content = True

            content = pool[
                position
            ]

            if content.id in seen_ids:

                continue

            seen_ids.add(
                content.id
            )

            merged.append(
                content
            )

            if len(merged) >= limit:

                break

        if not found_content:

            break

        position += 1

    return merged


# ============================================================
# BUILD DIGEST CANDIDATES
# ============================================================

def build_digest_candidates(
    user_id: str,
    period_start: str,
    period_end: str,
    candidate_limit_per_source: int = (
        DEFAULT_CANDIDATE_LIMIT_PER_SOURCE
    ),
    total_candidate_limit: int = (
        DEFAULT_TOTAL_CANDIDATE_LIMIT
    ),
) -> tuple[
    ExpertiseProfile,
    list[DigestContentCandidate],
]:

    profile = load_profile(
        user_id=user_id,
    )

    context = build_digest_candidate_context(
        profile=profile,
    )

    favorites_profile = (
        _build_favorites_profile(
            profile=profile,
        )
    )

    favorites_contents, _ = (
        select_contents(

            profile=favorites_profile,

            period_start=period_start,

            period_end=period_end,

            limit=(
                candidate_limit_per_source
            ),

            apply_profile_selection=True,

        )
    )

    profile_contents = []

    profile_expansion = (
        _build_profile_expansion_profile(
            profile=profile,
            context=context,
        )
    )

    if profile_expansion:

        profile_contents, _ = (
            select_contents(

                profile=profile_expansion,

                period_start=period_start,

                period_end=period_end,

                limit=(
                    candidate_limit_per_source
                ),

                apply_profile_selection=True,

            )
        )

    merged_contents = (
        _merge_content_pools(

            pools=[
                favorites_contents,
                profile_contents,
            ],

            limit=total_candidate_limit,

        )
    )

    candidates = [

        _build_candidate(
            content=content,
            context=context,
        )

        for content in merged_contents

    ]

    return (
        profile,
        candidates,
    )
