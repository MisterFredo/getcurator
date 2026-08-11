# backend/core/watch/watch_service.py

from core.expertise.service import (
    generate_expertise_from_profile,
)

from .watch_utils import (
    paginate,
    serialize_contents,
)

from core.user.user_service import (
    get_user,
)

from core.translation.drawer_translation_service import (
    translate_fields,
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
    universe_id: str | None = None,
    company_id: str | None = None,
    solution_id: str | None = None,
    topic_id: str | None = None,
):

    expertise = generate_expertise_from_profile(

        user_id=user_id,

        limit=limit + offset,

        universe_id=universe_id,

        company_id=company_id,

        solution_id=solution_id,

        topic_id=topic_id,

    )

    contents = paginate(

        contents=expertise.contents,

        limit=limit,

        offset=offset,

    )

    return {

        "items": serialize_contents(
            contents,
        ),

        "count": expertise.count,

    }


# ============================================================
# SEARCH
# ============================================================

def search(
    user_id: str,
    query: str,
    limit: int = 20,
    offset: int = 0,
    universe_id: str | None = None,
    company_id: str | None = None,
    solution_id: str | None = None,
    topic_id: str | None = None,
):

    expertise = generate_expertise_from_profile(

        user_id=user_id,

        query=query,

        limit=limit + offset,

        universe_id=universe_id,

        company_id=company_id,

        solution_id=solution_id,

        topic_id=topic_id,

    )

    contents = paginate(

        contents=expertise.contents,

        limit=limit,

        offset=offset,

    )

    return {

        "items": serialize_contents(
            contents,
        ),

        "count": expertise.count,

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

    if user_id:

        user = get_user(
            user_id,
        )

        if user:

            language = (
                user.get("LANGUAGE")
                or "fr"
            )

            if language != "fr":

                # ====================================================
                # PRE-TRANSLATED FIELDS
                # ====================================================

                content["TITLE"] = (

                    content.get(
                        "TITLE_EN",
                    )

                    or content.get(
                        "TITLE",
                    )

                )

                content["EXCERPT"] = (

                    content.get(
                        "EXCERPT_EN",
                    )

                    or content.get(
                        "EXCERPT",
                    )

                )

                # ====================================================
                # LIVE TRANSLATION
                # ====================================================

                translated = translate_fields(

                    {

                        "content_body":
                            content.get(
                                "CONTENT_BODY",
                                "",
                            ),

                        "signal_analytique":
                            content.get(
                                "SIGNAL_ANALYTIQUE",
                                "",
                            ),

                        "mecanique_expliquee":
                            content.get(
                                "MECANIQUE_EXPLIQUEE",
                                "",
                            ),

                        "enjeu_strategique":
                            content.get(
                                "ENJEU_STRATEGIQUE",
                                "",
                            ),

                        "point_de_friction":
                            content.get(
                                "POINT_DE_FRICTION",
                                "",
                            ),

                    },

                    language,

                )

                content = {

                    **content,

                    **translated,

                }

    # ========================================================
    # API MODEL
    # ========================================================

    return {

        "id_content":
            content.get(
                "ID_CONTENT",
            ),

        "source_id":
            content.get(
                "SOURCE_ID",
            ),

        "source_title":
            content.get(
                "SOURCE_TITLE",
            ),

        "source_url":
            content.get(
                "SOURCE_URL",
            ),

        "title":
            content.get(
                "TITLE",
            ),

        "title_en":
            content.get(
                "TITLE_EN",
            ),

        "excerpt":
            content.get(
                "EXCERPT",
            ),

        "excerpt_en":
            content.get(
                "EXCERPT_EN",
            ),

        "content_body":
            content.get(
                "content_body",
                content.get(
                    "CONTENT_BODY",
                ),
            ),

        "signal_analytique":
            content.get(
                "signal_analytique",
                content.get(
                    "SIGNAL_ANALYTIQUE",
                ),
            ),

        "mecanique_expliquee":
            content.get(
                "mecanique_expliquee",
                content.get(
                    "MECANIQUE_EXPLIQUEE",
                ),
            ),

        "enjeu_strategique":
            content.get(
                "enjeu_strategique",
                content.get(
                    "ENJEU_STRATEGIQUE",
                ),
            ),

        "point_de_friction":
            content.get(
                "point_de_friction",
                content.get(
                    "POINT_DE_FRICTION",
                ),
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
                "PUBLISHED_AT",
            ),

        "id_primary_company":
            content.get(
                "ID_PRIMARY_COMPANY",
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
