# backend/core/watch/watch_service.py

from core.expertise.service import (
    generate_expertise_from_profile,
)

from .serializer import (
    serialize_watch_contents,
    serialize_watch_content,
)


# ============================================================
# LATEST
# ============================================================

def latest(
    user_id: str,
    limit: int = 20,
    offset: int = 0,
    universe_id: str | None = None,
    feed_mode: str = "all",
):

    expertise = generate_expertise_from_profile(

        user_id=user_id,

        limit=limit,

    )

    return serialize_watch_contents(

        expertise.contents,

        offset=offset,

        limit=limit,

    )


# ============================================================
# SEARCH
# ============================================================

def search(
    query: str,
    user_id: str,
    limit: int = 20,
    offset: int = 0,
    universe_id: str | None = None,
    feed_mode: str = "all",
):

    raise NotImplementedError


# ============================================================
# CONTENT
# ============================================================

def get_content(
    content_id: str,
    user_id: str | None = None,
):

    raise NotImplementedError
