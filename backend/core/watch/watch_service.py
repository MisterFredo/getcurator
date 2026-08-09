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
):

    expertise = generate_expertise_from_profile(

        user_id=user_id,

        limit=limit + offset,

        universe_id=universe_id,

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
):

    expertise = generate_expertise_from_profile(

        user_id=user_id,

        query=query,

        limit=limit + offset,

        universe_id=universe_id,

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

    if not user_id:

        return content

    user = get_user(
        user_id,
    )

    if not user:

        return content

    language = (
        user.get("LANGUAGE")
        or "fr"
    )

    if language == "fr":

        return content

    # ========================================================
    # TRANSLATION
    # ========================================================

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

    return {

        **content,

        **translated,

    }
