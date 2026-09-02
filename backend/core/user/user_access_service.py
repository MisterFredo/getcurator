import hashlib
import uuid
from datetime import datetime, timezone

from config import (
    BQ_PROJECT,
    BQ_DATASET,
)

from utils.bigquery_utils import (
    query_bq,
)


TABLE_USER_ACCESS_EVENT = (
    f"{BQ_PROJECT}.{BQ_DATASET}."
    "RATECARD_USER_ACCESS_EVENT"
)


# ============================================================
# HELPERS
# ============================================================

def _hash_ip(
    ip_address: str | None,
) -> str | None:

    if not ip_address:
        return None

    return hashlib.sha256(
        ip_address.encode("utf-8")
    ).hexdigest()


def _detect_device_type(
    user_agent: str | None,
) -> str:

    if not user_agent:
        return "UNKNOWN"

    normalized = user_agent.lower()

    if any(
        value in normalized
        for value in [
            "ipad",
            "tablet",
        ]
    ):
        return "TABLET"

    if any(
        value in normalized
        for value in [
            "mobile",
            "iphone",
            "android",
        ]
    ):
        return "MOBILE"

    return "DESKTOP"


# ============================================================
# REGISTER SESSION
# ============================================================

def register_user_session(
    user_id: str,
    session_id: str,
    ip_address: str | None = None,
    user_agent: str | None = None,
):

    if not user_id:
        raise ValueError(
            "Missing user_id"
        )

    if not session_id:
        raise ValueError(
            "Missing session_id"
        )

    now = datetime.now(
        timezone.utc
    )

    # ========================================================
    # IDEMPOTENCY
    # One SESSION_START maximum per user/session
    # ========================================================

    sql = f"""

    INSERT INTO `{TABLE_USER_ACCESS_EVENT}` (

        ID_EVENT,
        ID_USER,
        EVENT_TYPE,
        SESSION_ID,
        ACCESS_AT,
        IP_HASH,
        USER_AGENT,
        DEVICE_TYPE,
        CREATED_AT

    )

    SELECT

        @id_event,
        @user_id,
        'SESSION_START',
        @session_id,
        @access_at,
        @ip_hash,
        @user_agent,
        @device_type,
        @created_at

    WHERE NOT EXISTS (

        SELECT 1

        FROM `{TABLE_USER_ACCESS_EVENT}`

        WHERE ID_USER = @user_id
          AND SESSION_ID = @session_id
          AND EVENT_TYPE = 'SESSION_START'

    )

    """

    params = {

        "id_event": str(
            uuid.uuid4()
        ),

        "user_id": user_id,

        "session_id": session_id,

        "access_at": now,

        "ip_hash": _hash_ip(
            ip_address
        ),

        "user_agent": (
            user_agent[:1000]
            if user_agent
            else None
        ),

        "device_type": _detect_device_type(
            user_agent
        ),

        "created_at": now,

    }

    query_bq(
        sql,
        params,
    )

    return {
        "status": "ok",
        "session_id": session_id,
    }
