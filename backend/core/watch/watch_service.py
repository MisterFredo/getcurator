# backend/core/watch/watch_service.py

from time import perf_counter

from core.expertise.service import (
    generate_expertise_from_profile,
)

from .watch_utils import (
    serialize_contents,
)

from core.user.user_service import (
    get_user,
)

from core.content.service import (
    get_content as load_content,
)


# ============================================================
# LATEST
# ============================================================

def latest(
    user_id: str,
    limit: int = 20,
    offset: int = 0,
    period_start: str | None = None,
    period_end: str | None = None,
    universe_id: str | None = None,
    company_id: str | None = None,
    solution_id: str | None = None,
    topic_id: str | None = None,
):

    t0 = perf_counter()

    expertise = generate_expertise_from_profile(

        user_id=user_id,

        period_start=period_start,

        period_end=period_end,

        limit=limit,

        offset=offset,

        universe_id=universe_id,

        company_id=company_id,

        solution_id=solution_id,

        topic_id=topic_id,
        apply_profile_selection=False,


    )

    t1 = perf_counter()

    items = serialize_contents(
        expertise.contents,
    )

    t2 = perf_counter()

    print(
        "⏱️ WATCH generate_expertise:",
        round(
            t1 - t0,
            3,
        ),
        "s",
    )

    print(
        "⏱️ WATCH serialize_contents:",
        round(
            t2 - t1,
            3,
        ),
        "s",
    )

    print(
        "⏱️ WATCH service TOTAL:",
        round(
            t2 - t0,
            3,
        ),
        "s",
    )

    return {

        "items":
            items,

        "count":
            expertise.count,

    }


# ============================================================
# SEARCH
# ============================================================

def search(
    user_id: str,
    query: str,
    limit: int = 20,
    offset: int = 0,
    period_start: str | None = None,
    period_end: str | None = None,
    universe_id: str | None = None,
    company_id: str | None = None,
    solution_id: str | None = None,
    topic_id: str | None = None,
):

    t0 = perf_counter()

    expertise = generate_expertise_from_profile(

        user_id=user_id,

        query=query,

        period_start=period_start,

        period_end=period_end,

        limit=limit,

        offset=offset,

        universe_id=universe_id,

        company_id=company_id,

        solution_id=solution_id,

        topic_id=topic_id,
        apply_profile_selection=False,


    )

    t1 = perf_counter()

    items = serialize_contents(
        expertise.contents,
    )

    t2 = perf_counter()

    print(
        "⏱️ WATCH SEARCH generate_expertise:",
        round(
            t1 - t0,
            3,
        ),
        "s",
    )

    print(
        "⏱️ WATCH SEARCH serialize_contents:",
        round(
            t2 - t1,
            3,
        ),
        "s",
    )

    print(
        "⏱️ WATCH SEARCH service TOTAL:",
        round(
            t2 - t0,
            3,
        ),
        "s",
    )

    return {

        "items":
            items,

        "count":
            expertise.count,

    }


# ============================================================
# CONTENT (DRAWER)
# ============================================================

def get_watch_content(
    content_id: str,
    user_id: str | None = None,
):

    content = load_content(
        content_id,
    )

    if not content:
        return None

    # ========================================================
    # USER LANGUAGE
    # ========================================================

    language = "fr"

    if user_id:

        user = get_user(
            user_id,
        )

        if user:

            language = (
                user.get(
                    "LANGUAGE"
                )
                or "fr"
            ).lower()

    # ========================================================
    # PERSISTED ENGLISH VERSION
    # ========================================================

    if language != "fr":

        content["TITLE"] = (

            content.get(
                "TITLE_EN"
            )

            or content.get(
                "TITLE"
            )
        )

        content["EXCERPT"] = (

            content.get(
                "EXCERPT_EN"
            )

            or content.get(
                "EXCERPT"
            )
        )

        content["CONTENT_BODY"] = (

            content.get(
                "CONTENT_BODY_EN"
            )

            or content.get(
                "CONTENT_BODY"
            )
        )

        content["SIGNAL_ANALYTIQUE"] = (

            content.get(
                "SIGNAL_ANALYTIQUE_EN"
            )

            or content.get(
                "SIGNAL_ANALYTIQUE"
            )
        )

        content["MECANIQUE_EXPLIQUEE"] = (

            content.get(
                "MECANIQUE_EXPLIQUEE_EN"
            )

            or content.get(
                "MECANIQUE_EXPLIQUEE"
            )
        )

        content["ENJEU_STRATEGIQUE"] = (

            content.get(
                "ENJEU_STRATEGIQUE_EN"
            )

            or content.get(
                "ENJEU_STRATEGIQUE"
            )
        )

        content["POINT_DE_FRICTION"] = (

            content.get(
                "POINT_DE_FRICTION_EN"
            )

            or content.get(
                "POINT_DE_FRICTION"
            )
        )

    # ========================================================
    # API MODEL
    # ========================================================

    return {

        "id_content":
            content.get(
                "ID_CONTENT"
            ),

        "source_id":
            content.get(
                "SOURCE_ID"
            ),

        "source_title":
            content.get(
                "SOURCE_TITLE"
            ),

        "source_url":
            content.get(
                "SOURCE_URL"
            ),

        "title":
            content.get(
                "TITLE"
            ),

        "title_en":
            content.get(
                "TITLE_EN"
            ),

        "excerpt":
            content.get(
                "EXCERPT"
            ),

        "excerpt_en":
            content.get(
                "EXCERPT_EN"
            ),

        "content_body":
            content.get(
                "CONTENT_BODY"
            ),

        "signal_analytique":
            content.get(
                "SIGNAL_ANALYTIQUE"
            ),

        "mecanique_expliquee":
            content.get(
                "MECANIQUE_EXPLIQUEE"
            ),

        "enjeu_strategique":
            content.get(
                "ENJEU_STRATEGIQUE"
            ),

        "point_de_friction":
            content.get(
                "POINT_DE_FRICTION"
            ),

        "chiffres":
            content.get(
                "CHIFFRES",
                [],
            ),

        "acteurs_cites":
            content.get(
                "ACTEURS_CITES",
                [],
            ),

        "published_at":
            content.get(
                "PUBLISHED_AT"
            ),

        "id_primary_company":
            content.get(
                "ID_PRIMARY_COMPANY"
            ),

        "companies":
            content.get(
                "COMPANIES",
                [],
            ),

        "solutions":
            content.get(
                "SOLUTIONS",
                [],
            ),

        "topics":
            content.get(
                "TOPICS",
                [],
            ),

        "universes":
            content.get(
                "UNIVERSES",
                [],
            ),

        "concepts":
            content.get(
                "CONCEPTS",
                [],
            ),

    }
