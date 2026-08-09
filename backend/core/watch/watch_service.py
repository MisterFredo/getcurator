from core.expertise.service import (
    generate_expertise_from_profile,
)

from .watch_utils import (
    paginate,
    serialize_contents,
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

    raise NotImplementedError
