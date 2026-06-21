from typing import (
    Dict,
    Any,
    List,
)

# ============================================================
# CREATE DIGEST
# ============================================================

def create_digest(
    user_id: str,
    digest_name: str,
    period_start: str,
    period_end: str,
) -> Dict[str, Any]:

    pass


# ============================================================
# LIST DIGESTS
# ============================================================

def list_digests(
    user_id: str,
) -> List[Dict[str, Any]]:

    pass


# ============================================================
# GET DIGEST
# ============================================================

def get_digest(
    digest_id: str,
) -> Dict[str, Any]:

    pass


# ============================================================
# DELETE DIGEST
# ============================================================

def delete_digest(
    digest_id: str,
) -> Dict[str, Any]:

    pass


# ============================================================
# GENERATE SUMMARY
# ============================================================

def generate_summary(
    digest_id: str,
) -> Dict[str, Any]:

    pass


# ============================================================
# SEND DIGEST
# ============================================================

def send_digest(
    digest_id: str,
) -> Dict[str, Any]:

    pass
