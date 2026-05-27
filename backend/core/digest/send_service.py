# backend/core/digest/send_service.py

import uuid

from datetime import (
    datetime,
    timezone,
)

from utils.bigquery_utils import (
    insert_rows_bq,
)

from config import (
    BQ_PROJECT,
    BQ_DATASET,
)

# ============================================================
# TABLE
# ============================================================

TABLE_DIGEST_SEND = f"""
{BQ_PROJECT}.{BQ_DATASET}.RATECARD_DIGEST_SEND
"""

# ============================================================
# LOG DIGEST SEND
# ============================================================

def log_digest_send(
    user_id: str,

    nb_contents: int,

    sent_by: str,

    subject: str = "",
):

    row = {
        "ID_DIGEST_SEND":
            str(uuid.uuid4()),

        "ID_USER":
            user_id,

        "SENT_AT":
            datetime.now(
                timezone.utc
            ).isoformat(),

        "NB_CONTENTS":
            nb_contents,

        "SENT_BY":
            sent_by,

        "SUBJECT":
            subject,
    }

    insert_rows_bq(
        TABLE_DIGEST_SEND,
        [row],
    )

    return {
        "success": True,
    }
