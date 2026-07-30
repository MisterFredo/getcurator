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
)


# ============================================================
# SELECT CONTENTS
# ============================================================

def select_contents(
    profile: ExpertiseProfile,
    period_start: str | None = None,
    period_end: str | None = None,
    limit: int | None = None,
) -> list[ExpertiseContent]:

    sql, params = build_selection_query(

        profile=profile,

        period_start=period_start,

        period_end=period_end,

        limit=limit,

    )

    rows = query_bq(

        sql=sql,

        params=params,

    )

    print("=" * 80)
    print("ROWS RETURNED :", len(rows))

    if rows:
        print("FIRST ROW")
        print(rows[0])
    else:
        print("NO ROWS RETURNED")

    print("=" * 80)

    return normalize_contents(
        rows
    )
