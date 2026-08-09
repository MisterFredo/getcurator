# backend/core/watch/watch_service.py

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
    feed_mode: str = "all",
):

    expertise = generate_expertise_from_profile(

        user_id=user_id,

        limit=limit + offset,

    )

    contents = paginate(

        expertise.contents,

        limit=limit,

        offset=offset,

    )

    return {

        "items": serialize_contents(
            contents,
        ),

        "count": expertise.count,

    }
