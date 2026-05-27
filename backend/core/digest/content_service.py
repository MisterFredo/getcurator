from typing import (
    Optional,
    List,
    Dict,
    Any,
)

from core.curator.service import (
    latest,
    search,
)

# ============================================================
# CONTENTS
# ============================================================

def search_digest_content(
    query: Optional[str] = None,

    limit: int = 20,
    offset: int = 0,

    user_id: Optional[str] = None,

    universe_id: Optional[str] = None,

    content_type: Optional[str] = None,

    feed_mode: Optional[str] = None,

    blocks_config: Optional[
        Dict[str, Any]
    ] = None,
) -> Dict[str, Any]:

    # ========================================================
    # BLOCK CONFIG
    # ========================================================

    def get_block(name: str):

        if not blocks_config:
            return None

        return (
            blocks_config.get(name)
            or {}
        )

    def resolve_limit(block):

        if not block:
            return limit

        return block.get(
            "limit",
            limit,
        )

    def resolve_content_type(block):

        if not block:
            return content_type

        return block.get(
            "content_type",
            content_type,
        )

    def resolve_feed_mode(block):

        if not block:
            return feed_mode

        return block.get(
            "feed_mode",
            feed_mode,
        )

    def resolve_universe(block):

        if not block:
            return universe_id

        return block.get(
            "universe_id",
            universe_id,
        )

    # ========================================================
    # MAIN CONTENTS BLOCK
    # ========================================================

    contents_block = get_block(
        "contents"
    )

    contents_limit = resolve_limit(
        contents_block
    )

    contents_type = (
        resolve_content_type(
            contents_block
        )
    )

    contents_feed_mode = (
        resolve_feed_mode(
            contents_block
        )
    )

    contents_universe = (
        resolve_universe(
            contents_block
        )
    )

    # ========================================================
    # SEARCH MODE
    # ========================================================

    if query and query.strip():

        contents = search(
            q=query,

            limit=contents_limit,

            offset=offset,

            user_id=user_id,

            universe_id=contents_universe,

            content_type=contents_type,

            feed_mode=contents_feed_mode,
        )

    # ========================================================
    # LATEST MODE
    # ========================================================

    else:

        contents = latest(
            limit=contents_limit,

            offset=offset,

            user_id=user_id,

            universe_id=contents_universe,

            content_type=contents_type,

            feed_mode=contents_feed_mode,
        )

    # ========================================================
    # RESPONSE
    # ========================================================

    return {
        "contents": contents,
    }
}
