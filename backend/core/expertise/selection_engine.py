# backend/core/expertise/selection_engine.py

from api.expertise.models import (
    ExpertiseContent,
    ExpertiseProfile,
)

from utils.bigquery_utils import (
    query_bq,
)

from .content_mapper import (
    normalize_contents,
)

from .query_builder import (
    build_selection_query,
    build_selection_count_query,
)


# ============================================================
# SELECT CONTENTS
# ============================================================

def select_contents(
    profile: ExpertiseProfile,
    period_start: str | None = None,
    period_end: str | None = None,
    limit: int | None = None,
    offset: int = 0,
    universe_id: str | None = None,
    query: str | None = None,
    company_id: str | None = None,
    solution_id: str | None = None,
    topic_id: str | None = None,
    apply_profile_selection: bool = True,
) -> tuple[
    list[ExpertiseContent],
    int,
]:

    # ========================================================
    # CONTENT QUERY
    # ========================================================

    sql, params = build_selection_query(

        profile=profile,

        period_start=period_start,

        period_end=period_end,

        limit=limit,

        offset=offset,

        universe_id=universe_id,

        query=query,

        company_id=company_id,

        solution_id=solution_id,

        topic_id=topic_id,

        apply_profile_selection=apply_profile_selection,

    )

    rows = query_bq(

        sql=sql,

        params=params,

    )

    contents = normalize_contents(
        rows,
    )

    # ========================================================
    # COUNT QUERY
    # ========================================================

    count_sql, count_params = (
        build_selection_count_query(

            profile=profile,

            period_start=period_start,

            period_end=period_end,

            universe_id=universe_id,

            query=query,

            company_id=company_id,

            solution_id=solution_id,

            topic_id=topic_id,

            apply_profile_selection=apply_profile_selection,

        )
    )

    count_rows = query_bq(

        sql=count_sql,

        params=count_params,

    )

    total = (

        int(
            count_rows[0].get(
                "total",
                0,
            )
        )

        if count_rows

        else 0

    )

    return (
        contents,
        total,
    )
