from dataclasses import (
    dataclass,
    field,
)

from datetime import (
    datetime,
    timedelta,
    timezone,
)

from typing import (
    Callable,
)

from api.expertise.models import (
    ExpertiseContent,
)

from core.expertise.selection_engine import (
    select_contents,
)

from core.touch.search_models import (
    TouchCandidateSource,
    TouchContentCandidate,
    TouchEntityReference,
    TouchResearchBrief,
    TouchResearchInterpretation,
)


# ============================================================
# CONFIGURATION
# ============================================================

DEFAULT_TOUCH_CANDIDATE_LIMIT_PER_POOL = 40

DEFAULT_TOUCH_TOTAL_CANDIDATE_LIMIT = 100

DEFAULT_TOUCH_MAX_CORE_ENTITIES = 12

DEFAULT_TOUCH_MAX_SEARCH_TERMS = 10

DEFAULT_TOUCH_MAX_RELATED_ANGLES = 6


# ============================================================
# INTERNAL MATCH
# ============================================================

@dataclass
class TouchCandidateMatch:

    selection_sources: set[
        TouchCandidateSource
    ] = field(
        default_factory=set,
    )

    matched_entities: set[str] = field(
        default_factory=set,
    )

    matched_terms: set[str] = field(
        default_factory=set,
    )

    matched_angles: set[str] = field(
        default_factory=set,
    )


# ============================================================
# INTERNAL POOL
# ============================================================

@dataclass
class TouchCandidatePool:

    contents: list[
        ExpertiseContent
    ]

    selection_source: (
        TouchCandidateSource
    )

    matched_entity: str = ""

    matched_term: str = ""

    matched_angle: str = ""


# ============================================================
# NORMALIZE LANGUAGE
# ============================================================

def _normalize_language(
    language: str,
) -> str:

    normalized = (
        language
        .strip()
        .lower()
    )

    if normalized.startswith(
        "en"
    ):

        return "en"

    return "fr"


# ============================================================
# PERIOD VALUE
# ============================================================

def _period_value(
    value,
) -> str | None:

    if value is None:

        return None

    if hasattr(
        value,
        "isoformat",
    ):

        return value.isoformat()

    return str(
        value
    )


# ============================================================
# CLEAN TEXT
# ============================================================

def _clean_text(
    value,
) -> str:

    if not isinstance(
        value,
        str,
    ):

        return ""

    return value.strip()


# ============================================================
# SAFE LIST
# ============================================================

def _safe_list(
    value,
) -> list:

    if isinstance(
        value,
        list,
    ):

        return value

    return []


# ============================================================
# UNIQUE ENTITIES
# ============================================================

def _unique_entities(
    entities: list[
        TouchEntityReference
    ],
) -> list[
    TouchEntityReference
]:

    unique_entities = []

    seen_entities = set()

    for entity in entities:

        key = (
            entity.entity_type,
            entity.entity_id,
        )

        if key in seen_entities:

            continue

        seen_entities.add(
            key
        )

        unique_entities.append(
            entity
        )

    return unique_entities


# ============================================================
# UNIQUE TEXT VALUES
# ============================================================

def _unique_text_values(
    values: list[str],
) -> list[str]:

    unique_values = []

    seen_values = set()

    for value in values:

        cleaned_value = _clean_text(
            value
        )

        if not cleaned_value:

            continue

        key = cleaned_value.casefold()

        if key in seen_values:

            continue

        seen_values.add(
            key
        )

        unique_values.append(
            cleaned_value
        )

    return unique_values


# ============================================================
# SEARCH CONTENT POOL
# ============================================================

def _search_content_pool(
    brief: TouchResearchBrief,
    language: str,
    limit: int,
    query: str | None = None,
    company_id: str | None = None,
    solution_id: str | None = None,
    topic_id: str | None = None,
) -> list[ExpertiseContent]:

    selection_args = {
        "profile": None,
        "period_start": _period_value(
            brief.period_start
        ),
        "period_end": _period_value(
            brief.period_end
        ),
        "limit": limit,
        "offset": 0,
        "query": query,
        "company_id": company_id,
        "solution_id": solution_id,
        "topic_id": topic_id,
        "apply_profile_selection": False,
        "allowed_universe_ids": None,
        "language": language,
        "include_total": False,
    }

    monthly_quota = None

    if brief.period_start:

        start = brief.period_start

        if start.tzinfo is None:
            start = start.replace(
                tzinfo=timezone.utc
            )
        else:
            start = start.astimezone(
                timezone.utc
            )

        end = (
            brief.period_end
            or datetime.now(timezone.utc)
        )

        if end.tzinfo is None:
            end = end.replace(
                tzinfo=timezone.utc
            )
        else:
            end = end.astimezone(
                timezone.utc
            )

        # Ne réserve pas de places à des mois futurs.
        end = min(
            end,
            datetime.now(timezone.utc),
        )

        if end > start:

            last_included = (
                end
                - timedelta(
                    microseconds=1
                )
            )

            month_count = (
                (
                    last_included.year
                    - start.year
                ) * 12
                + last_included.month
                - start.month
                + 1
            )

            if month_count > 1:

                monthly_quota = max(
                    1,
                    (
                        limit
                        + month_count
                        - 1
                    ) // month_count,
                )

    contents, _ = select_contents(
        **selection_args,
        monthly_quota=monthly_quota,
    )

    if (
        monthly_quota is None
        or len(contents) >= limit
    ):
        return contents

    # Si certains mois sont peu fournis, complète
    # jusqu'à la limite avec le tri habituel.
    recent_contents, _ = select_contents(
        **selection_args,
    )

    seen_ids = {
        content.id
        for content in contents
    }

    for content in recent_contents:

        if content.id in seen_ids:
            continue

        contents.append(content)
        seen_ids.add(content.id)

        if len(contents) >= limit:
            break

    return contents


# ============================================================
# REGISTER POOL MATCHES
# ============================================================

def _register_pool_matches(
    pool: TouchCandidatePool,
    matches_by_content_id: dict[
        str,
        TouchCandidateMatch
    ],
    contents_by_id: dict[
        str,
        ExpertiseContent
    ],
) -> None:

    for content in pool.contents:

        content_id = content.id

        contents_by_id[
            content_id
        ] = content

        match = (
            matches_by_content_id
            .setdefault(
                content_id,
                TouchCandidateMatch(),
            )
        )

        match.selection_sources.add(
            pool.selection_source
        )

        if pool.matched_entity:

            match.matched_entities.add(
                pool.matched_entity
            )

        if pool.matched_term:

            match.matched_terms.add(
                pool.matched_term
            )

        if pool.matched_angle:

            match.matched_angles.add(
                pool.matched_angle
            )


# ============================================================
# MERGE CONTENT POOLS
# ============================================================

def _merge_content_pools(
    pools: list[
        TouchCandidatePool
    ],
    excluded_content_ids: set[str],
    total_limit: int,
) -> list[str]:

    merged_content_ids = []

    seen_content_ids = set(
        excluded_content_ids
    )

    position = 0

    while (
        len(
            merged_content_ids
        )
        < total_limit
    ):

        found_content = False

        for pool in pools:

            if position >= len(
                pool.contents
            ):

                continue

            found_content = True

            content = pool.contents[
                position
            ]

            if content.id in seen_content_ids:

                continue

            seen_content_ids.add(
                content.id
            )

            merged_content_ids.append(
                content.id
            )

            if (
                len(
                    merged_content_ids
                )
                >= total_limit
            ):

                break

        if not found_content:

            break

        position += 1

    return merged_content_ids


# ============================================================
# BUILD TOUCH CANDIDATE
# ============================================================

def _build_touch_candidate(
    content: ExpertiseContent,
    match: TouchCandidateMatch,
) -> TouchContentCandidate:

    return TouchContentCandidate(

        content_id=content.id,

        title=_clean_text(
            content.title
        ),

        excerpt=_clean_text(
            content.excerpt
        ),

        source_title=_clean_text(
            content.source_title
        ),

        source_url=_clean_text(
            content.source_url
        ),

        published_at=content.published_at,

        content_body=_clean_text(
            content.content_body
        ),

        signal_analytique=_clean_text(
            content.signal
        ),

        mecanique_expliquee=_clean_text(
            content.mecanique
        ),

        enjeu_strategique=_clean_text(
            content.enjeu
        ),

        point_de_friction=_clean_text(
            content.friction
        ),

        chiffres=_safe_list(
            content.chiffres
        ),

        companies=_safe_list(
            content.companies
        ),

        solutions=_safe_list(
            content.solutions
        ),

        topics=_safe_list(
            content.topics
        ),

        universes=_safe_list(
            content.universes
        ),

        concepts=_safe_list(
            content.concepts
        ),

        selection_sources=sorted(
            match.selection_sources
        ),

        matched_entities=sorted(
            match.matched_entities
        ),

        matched_terms=sorted(
            match.matched_terms
        ),

        matched_angles=sorted(
            match.matched_angles
        ),

    )


# ============================================================
# ADD ENTITY POOLS
# ============================================================

def _add_entity_pools(
    brief: TouchResearchBrief,
    interpretation: (
        TouchResearchInterpretation
    ),
    language: str,
    limit_per_pool: int,
    pools: list[
        TouchCandidatePool
    ],
    errors: list[str],
) -> None:

    entity_groups: list[
        tuple[
            list[TouchEntityReference],
            TouchCandidateSource,
            Callable,
        ]
    ] = [

        (
            interpretation.companies,
            "CORE_COMPANY",
            lambda entity: {
                "company_id":
                    entity.entity_id,
            },
        ),

        (
            interpretation.solutions,
            "CORE_SOLUTION",
            lambda entity: {
                "solution_id":
                    entity.entity_id,
            },
        ),

        (
            interpretation.topics,
            "CORE_TOPIC",
            lambda entity: {
                "topic_id":
                    entity.entity_id,
            },
        ),

    ]

    remaining_entity_slots = (
        DEFAULT_TOUCH_MAX_CORE_ENTITIES
    )

    for (
        entities,
        selection_source,
        build_filter,
    ) in entity_groups:

        if remaining_entity_slots <= 0:

            break

        unique_entities = (
            _unique_entities(
                entities
            )
        )

        retained_entities = (
            unique_entities[
                :remaining_entity_slots
            ]
        )

        remaining_entity_slots -= len(
            retained_entities
        )

        for entity in retained_entities:

            try:

                contents = _search_content_pool(

                    brief=brief,

                    language=language,

                    limit=limit_per_pool,

                    **build_filter(
                        entity
                    ),

                )

                pools.append(

                    TouchCandidatePool(

                        contents=contents,

                        selection_source=(
                            selection_source
                        ),

                        matched_entity=(
                            entity.entity_label
                        ),

                    )

                )

            except Exception as exc:

                errors.append(

                    "Échec de la recherche pour "
                    f"{entity.entity_label}: "
                    f"{str(exc)[:500]}"

                )


# ============================================================
# ADD SEARCH TERM POOLS
# ============================================================

def _add_search_term_pools(
    brief: TouchResearchBrief,
    interpretation: (
        TouchResearchInterpretation
    ),
    language: str,
    limit_per_pool: int,
    pools: list[
        TouchCandidatePool
    ],
    errors: list[str],
) -> None:

    search_terms = (
        _unique_text_values(
            interpretation.search_terms
        )
        [
            :DEFAULT_TOUCH_MAX_SEARCH_TERMS
        ]
    )

    for search_term in search_terms:

        try:

            contents = _search_content_pool(

                brief=brief,

                language=language,

                limit=limit_per_pool,

                query=search_term,

            )

            pools.append(

                TouchCandidatePool(

                    contents=contents,

                    selection_source=(
                        "SEARCH_TERM"
                    ),

                    matched_term=search_term,

                )

            )

        except Exception as exc:

            errors.append(

                "Échec de la recherche pour "
                f"le terme {search_term}: "
                f"{str(exc)[:500]}"

            )


# ============================================================
# ADD RELATED ANGLE POOLS
# ============================================================

def _add_related_angle_pools(
    brief: TouchResearchBrief,
    interpretation: (
        TouchResearchInterpretation
    ),
    language: str,
    limit_per_pool: int,
    pools: list[
        TouchCandidatePool
    ],
    errors: list[str],
) -> None:

    related_angles = (
        _unique_text_values(
            interpretation.related_angles
        )
        [
            :DEFAULT_TOUCH_MAX_RELATED_ANGLES
        ]
    )

    for related_angle in related_angles:

        try:

            contents = _search_content_pool(

                brief=brief,

                language=language,

                limit=limit_per_pool,

                query=related_angle,

            )

            pools.append(

                TouchCandidatePool(

                    contents=contents,

                    selection_source=(
                        "RELATED_ANGLE"
                    ),

                    matched_angle=related_angle,

                )

            )

        except Exception as exc:

            errors.append(

                "Échec de la recherche pour "
                f"l’angle {related_angle}: "
                f"{str(exc)[:500]}"

            )


# ============================================================
# BUILD TOUCH CANDIDATES
# ============================================================

def build_touch_candidates(
    brief: TouchResearchBrief,
    interpretation: (
        TouchResearchInterpretation
    ),
    candidate_limit_per_pool: int = (
        DEFAULT_TOUCH_CANDIDATE_LIMIT_PER_POOL
    ),
    total_candidate_limit: int = (
        DEFAULT_TOUCH_TOTAL_CANDIDATE_LIMIT
    ),
) -> tuple[
    list[TouchContentCandidate],
    list[str],
]:

    candidate_limit_per_pool = max(
        1,
        candidate_limit_per_pool,
    )

    total_candidate_limit = max(
        1,
        total_candidate_limit,
    )

    language = _normalize_language(
        brief.output_language
    )

    pools: list[
        TouchCandidatePool
    ] = []

    errors: list[str] = []

    # ========================================================
    # CORE ENTITY POOLS
    # ========================================================

    _add_entity_pools(

        brief=brief,

        interpretation=interpretation,

        language=language,

        limit_per_pool=(
            candidate_limit_per_pool
        ),

        pools=pools,

        errors=errors,

    )

    # ========================================================
    # SEARCH TERM POOLS
    # ========================================================

    _add_search_term_pools(

        brief=brief,

        interpretation=interpretation,

        language=language,

        limit_per_pool=(
            candidate_limit_per_pool
        ),

        pools=pools,

        errors=errors,

    )

    # ========================================================
    # MATCH METADATA
    # ========================================================

    matches_by_content_id: dict[
        str,
        TouchCandidateMatch
    ] = {}

    contents_by_id: dict[
        str,
        ExpertiseContent
    ] = {}

    for pool in pools:

        _register_pool_matches(

            pool=pool,

            matches_by_content_id=(
                matches_by_content_id
            ),

            contents_by_id=(
                contents_by_id
            ),

        )

    # ========================================================
    # EXCLUDED CONTENTS
    # ========================================================

    excluded_content_ids = set(

        brief.previously_proposed_content_ids

        + brief.selected_content_ids

        + brief.dismissed_content_ids

    )

    # ========================================================
    # BALANCED MERGE
    # ========================================================

    merged_content_ids = (
        _merge_content_pools(

            pools=pools,

            excluded_content_ids=(
                excluded_content_ids
            ),

            total_limit=(
                total_candidate_limit
            ),

        )
    )

    # ========================================================
    # CANDIDATES
    # ========================================================

    candidates = [

        _build_touch_candidate(

            content=contents_by_id[
                content_id
            ],

            match=matches_by_content_id[
                content_id
            ],

        )

        for content_id in merged_content_ids

    ]

    return (
        candidates,
        errors,
    )
