import base64
import hashlib
import hmac
import json
import os
import secrets

from datetime import (
    datetime,
    timedelta,
    timezone,
)

from typing import (
    Any,
)

from pydantic import (
    ValidationError,
)

from core.feedback.models import (
    DigestFeedbackTokenPayload,
)


# ============================================================
# CONFIGURATION
# ============================================================

DIGEST_FEEDBACK_TOKEN_VERSION = "1"

DIGEST_FEEDBACK_TOKEN_TTL_DAYS = 45

DIGEST_FEEDBACK_SECRET_ENV = (
    "DIGEST_FEEDBACK_SECRET"
)


# ============================================================
# EXCEPTIONS
# ============================================================

class DigestFeedbackTokenError(
    ValueError,
):
    """
    Base exception for invalid Digest feedback tokens.
    """


class DigestFeedbackTokenExpiredError(
    DigestFeedbackTokenError,
):
    """
    Raised when a valid token has expired.
    """


# ============================================================
# BASE64
# ============================================================

def _base64url_encode(
    value: bytes,
) -> str:

    return (
        base64
        .urlsafe_b64encode(
            value
        )
        .decode(
            "ascii"
        )
        .rstrip(
            "="
        )
    )


def _base64url_decode(
    value: str,
) -> bytes:

    padding_length = (
        -len(value)
        % 4
    )

    padded_value = (
        value
        + (
            "="
            * padding_length
        )
    )

    try:

        return (
            base64
            .urlsafe_b64decode(
                padded_value.encode(
                    "ascii"
                )
            )
        )

    except Exception as exc:

        raise DigestFeedbackTokenError(
            "Invalid feedback token encoding"
        ) from exc


# ============================================================
# SECRET
# ============================================================

def _get_feedback_secret() -> bytes:

    secret = (
        os.getenv(
            DIGEST_FEEDBACK_SECRET_ENV
        )
        or ""
    ).strip()

    if not secret:

        raise RuntimeError(
            (
                "Missing required environment variable: "
                f"{DIGEST_FEEDBACK_SECRET_ENV}"
            )
        )

    if len(secret) < 32:

        raise RuntimeError(
            (
                f"{DIGEST_FEEDBACK_SECRET_ENV} "
                "must contain at least 32 characters"
            )
        )

    return secret.encode(
        "utf-8"
    )


# ============================================================
# SIGNATURE
# ============================================================

def _build_signature(
    encoded_payload: str,
) -> str:

    digest = hmac.new(

        key=_get_feedback_secret(),

        msg=encoded_payload.encode(
            "ascii"
        ),

        digestmod=hashlib.sha256,

    ).digest()

    return _base64url_encode(
        digest
    )


# ============================================================
# SERIALIZE
# ============================================================

def _serialize_payload(
    payload: dict[
        str,
        Any,
    ],
) -> str:

    serialized_payload = json.dumps(

        payload,

        ensure_ascii=False,

        sort_keys=True,

        separators=(
            ",",
            ":",
        ),

    ).encode(
        "utf-8"
    )

    return _base64url_encode(
        serialized_payload
    )


# ============================================================
# PARSE
# ============================================================

def _parse_payload(
    encoded_payload: str,
) -> dict[
    str,
    Any,
]:

    raw_payload = _base64url_decode(
        encoded_payload
    )

    try:

        payload = json.loads(
            raw_payload.decode(
                "utf-8"
            )
        )

    except (
        UnicodeDecodeError,
        json.JSONDecodeError,
    ) as exc:

        raise DigestFeedbackTokenError(
            "Invalid feedback token payload"
        ) from exc

    if not isinstance(
        payload,
        dict,
    ):

        raise DigestFeedbackTokenError(
            "Invalid feedback token payload"
        )

    return payload


# ============================================================
# GENERATE TOKEN
# ============================================================

def generate_digest_feedback_token(
    user_id: str,
    digest_id: str,
    content_id: str,
    ttl_days: int = (
        DIGEST_FEEDBACK_TOKEN_TTL_DAYS
    ),
) -> str:

    if not user_id:

        raise ValueError(
            "user_id is required"
        )

    if not digest_id:

        raise ValueError(
            "digest_id is required"
        )

    if not content_id:

        raise ValueError(
            "content_id is required"
        )

    now = datetime.now(
        timezone.utc
    )

    expires_at = (
        now
        + timedelta(
            days=max(
                1,
                ttl_days,
            )
        )
    )

    payload = {

        "version":
            DIGEST_FEEDBACK_TOKEN_VERSION,

        "user_id":
            user_id,

        "digest_id":
            digest_id,

        "content_id":
            content_id,

        "feedback_type":
            "NOT_RELEVANT",

        "issued_at":
            int(
                now.timestamp()
            ),

        "expires_at":
            int(
                expires_at.timestamp()
            ),

        "nonce":
            secrets.token_urlsafe(
                12
            ),

    }

    encoded_payload = (
        _serialize_payload(
            payload
        )
    )

    signature = _build_signature(
        encoded_payload
    )

    return (
        f"{encoded_payload}"
        f".{signature}"
    )


# ============================================================
# VERIFY TOKEN
# ============================================================

def verify_digest_feedback_token(
    token: str,
) -> DigestFeedbackTokenPayload:

    cleaned_token = (
        token.strip()
        if isinstance(
            token,
            str,
        )
        else ""
    )

    if not cleaned_token:

        raise DigestFeedbackTokenError(
            "Feedback token is required"
        )

    token_parts = cleaned_token.split(
        "."
    )

    if len(token_parts) != 2:

        raise DigestFeedbackTokenError(
            "Invalid feedback token"
        )

    (
        encoded_payload,
        supplied_signature,
    ) = token_parts

    expected_signature = (
        _build_signature(
            encoded_payload
        )
    )

    if not hmac.compare_digest(
        supplied_signature,
        expected_signature,
    ):

        raise DigestFeedbackTokenError(
            "Invalid feedback token signature"
        )

    payload = _parse_payload(
        encoded_payload
    )

    if (
        payload.get(
            "version"
        )
        != DIGEST_FEEDBACK_TOKEN_VERSION
    ):

        raise DigestFeedbackTokenError(
            "Unsupported feedback token version"
        )

    expires_at = payload.get(
        "expires_at"
    )

    if not isinstance(
        expires_at,
        int,
    ):

        raise DigestFeedbackTokenError(
            "Invalid feedback token expiration"
        )

    now_timestamp = int(
        datetime.now(
            timezone.utc
        ).timestamp()
    )

    if expires_at < now_timestamp:

        raise DigestFeedbackTokenExpiredError(
            "Feedback token has expired"
        )

    try:

        return (
            DigestFeedbackTokenPayload
            .model_validate(
                {
                    "user_id":
                        payload.get(
                            "user_id"
                        ),

                    "digest_id":
                        payload.get(
                            "digest_id"
                        ),

                    "content_id":
                        payload.get(
                            "content_id"
                        ),

                    "feedback_type":
                        payload.get(
                            "feedback_type"
                        ),
                }
            )
        )

    except ValidationError as exc:

        raise DigestFeedbackTokenError(
            "Invalid feedback token data"
        ) from exc
