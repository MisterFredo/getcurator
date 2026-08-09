# ============================================================
# LATEST
# ============================================================

from core.expertise.service import (
    generate_expertise_from_profile,
)

from core.watch.watch_utils import (
    paginate,
    serialize_contents,
)


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
