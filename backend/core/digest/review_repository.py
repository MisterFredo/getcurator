from google.cloud import bigquery

from config import (
    BQ_PROJECT,
    BQ_DATASET,
)

from utils.bigquery_utils import (
    query_bq,
    update_bq,
    get_bigquery_client,
)

from core.digest.models import (
    DigestReview,
)

TABLE_REVIEW = (
    f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_DIGEST_REVIEW"
)

# ============================================================
# CREATE
# ============================================================

def insert_review(
    review: DigestReview,
) -> DigestReview:
    """
    Persist a new DigestReview.
    """

    row = [{

        "ID": review.id,

        "USER_ID": review.request.user_id,

        "LANGUAGE": review.knowledge.expertise.profile.language,

        "PERIOD_START": review.request.period_start.isoformat(),
        "PERIOD_END": review.request.period_end.isoformat(),

        "TOTAL_CONTENTS": review.total_contents,
        "ANALYZED_CONTENTS": review.analyzed_contents,

        "KNOWLEDGE_JSON": review.knowledge.model_dump(),

        "CREATED_AT": review.created_at.isoformat(),

    }]

    client = get_bigquery_client()

    client.load_table_from_json(

        row,

        TABLE_REVIEW,

        job_config=bigquery.LoadJobConfig(

            write_disposition="WRITE_APPEND",

        ),

    ).result()

    return review

# ============================================================
# UPDATE
# ============================================================

def update_review(
    review: DigestReview,
) -> DigestReview:
    """
    Update an existing DigestReview.
    """

    update_bq(

        table=TABLE_REVIEW,

        fields={

            "USER_ID": review.request.user_id,

            "LANGUAGE": review.knowledge.expertise.profile.language,

            "PERIOD_START": review.request.period_start,

            "PERIOD_END": review.request.period_end,

            "TOTAL_CONTENTS": review.total_contents,

            "ANALYZED_CONTENTS": review.analyzed_contents,

            "KNOWLEDGE_JSON": review.knowledge.model_dump(),

            "CREATED_AT": review.created_at,

        },

        where={

            "ID": review.id,

        },

    )

    return review

# ============================================================
# GET
# ============================================================

def fetch_review(
    review_id: str,
) -> DigestReview | None:
    """
    Return a DigestReview by id.
    """

    raise NotImplementedError(
        "KnowledgeResult deserialization not implemented yet."
    )

# ============================================================
# LIST
# ============================================================

def fetch_reviews() -> list[DigestReview]:
    """
    Return the latest DigestReviews.
    """

    raise NotImplementedError(
        "KnowledgeResult deserialization not implemented yet."
    )
