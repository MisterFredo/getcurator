from core.expertise.service import (
    generate_expertise_from_profile,
)

from .watch_utils import (
    paginate,
    serialize_contents,
)

from core.content.content_service import (
    get_content,
)

from core.user.user_service import (
    get_user,
)

from core.translation.drawer_translation_service import (
    translate_fields,
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
# CONTENT
# ============================================================

def get_content(
    content_id: str,
    user_id: str | None = None,
):

    content = get_content(
        content_id,
    )

    if not content:

        return None

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

    translated = translate_fields(

        {

            "content_body":
                content.get(
                    "content_body",
                    "",
                ),

            "signal":
                content.get(
                    "signal",
                    "",
                ),

            "mecanique":
                content.get(
                    "mecanique",
                    "",
                ),

            "enjeu":
                content.get(
                    "enjeu",
                    "",
                ),

            "friction":
                content.get(
                    "friction",
                    "",
                ),

        },

        language,

    )

    return {

        **content,

        **translated,

    }
