from typing import Optional

# ============================================================
# LATEST
# ============================================================

def latest(
    user_id: str,
    limit: int = 20,
    offset: int = 0,
    universe_id: Optional[str] = None,
    feed_mode: str = "all",
):
    """
    Return the latest contents for Watch.
    """
    raise NotImplementedError


# ============================================================
# SEARCH
# ============================================================

def search(
    query: str,
    user_id: str,
    limit: int = 20,
    offset: int = 0,
    universe_id: Optional[str] = None,
    feed_mode: str = "all",
):
    """
    Search contents inside Watch.
    """
    raise NotImplementedError


# ============================================================
# CONTENT
# ============================================================

def get_content(
    content_id: str,
    user_id: Optional[str] = None,
):
    """
    Return one content for the Drawer.
    """
    raise NotImplementedError
