from typing import Optional

from config import (
    BQ_PROJECT,
    BQ_DATASET,
)

from utils.bigquery_utils import (
    query_bq,
)


# ============================================================
# TABLES
# ============================================================

TABLE_TOPIC = (
    f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_TOPIC"
)

TABLE_TOPIC_UNIVERSE = (
    f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_TOPIC_UNIVERSE"
)

TABLE_USER_UNIVERSE = (
    f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_USER_UNIVERSE"
)

TABLE_CONTENT_ENRICHED = (
    f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_CONTENT_ENRICHED"
)


# ============================================================
# PUBLIC VIEW
# ============================================================

def get_topic_view(
    topic_id: str,
) -> Optional[dict]:

    rows = query_bq(
        f"""
        SELECT

            ID_TOPIC,

            LABEL,

            TOPIC_AXIS,

            DESCRIPTION

        FROM `{TABLE_TOPIC}`

        WHERE ID_TOPIC = @topic_id

        LIMIT 1
        """,
        {
            "topic_id":
                topic_id,
        },
    )

    if not rows:

        return None

    topic = rows[0]

    return {

        "id_topic":
            topic.get(
                "ID_TOPIC",
            ),

        "label":
            topic.get(
                "LABEL",
            ),

        "topic_axis":
            topic.get(
                "TOPIC_AXIS",
            ),

        "description":
            topic.get(
                "DESCRIPTION",
            ),

    }


# ============================================================
# LIST CURATOR
# ============================================================

def list_topics_for_user(
    user_id: str,
):

    sql = f"""
    SELECT

        t.ID_TOPIC,

        t.LABEL,

        COALESCE(
            tc.CONTENT_COUNT,
            0
        ) AS CONTENT_COUNT,

        ARRAY_AGG(
            DISTINCT u.LABEL
            IGNORE NULLS
        ) AS UNIVERSES

    FROM `{TABLE_TOPIC}` t

    JOIN `{TABLE_TOPIC_UNIVERSE}` tu

        ON tu.ID_TOPIC =
            t.ID_TOPIC

    JOIN `{BQ_PROJECT}.{BQ_DATASET}.RATECARD_UNIVERSE` u

        ON u.ID_UNIVERSE =
            tu.ID_UNIVERSE

    JOIN `{TABLE_USER_UNIVERSE}` uu

        ON uu.ID_UNIVERSE =
            tu.ID_UNIVERSE

    LEFT JOIN (

        SELECT

            topic.id_topic
                AS ID_TOPIC,

            COUNT(
                DISTINCT content.ID_CONTENT
            ) AS CONTENT_COUNT

        FROM `{TABLE_CONTENT_ENRICHED}` content,

        UNNEST(
            content.TOPICS
        ) topic

        WHERE

            content.IS_ACTIVE = TRUE

            AND content.STATUS =
                "PUBLISHED"

        GROUP BY

            topic.id_topic

    ) tc

        ON tc.ID_TOPIC =
            t.ID_TOPIC

    WHERE

        t.IS_ACTIVE = TRUE

        AND uu.ID_USER =
            @user_id

    GROUP BY

        t.ID_TOPIC,

        t.LABEL,

        tc.CONTENT_COUNT

    ORDER BY

        UPPER(
            t.LABEL
        )
    """

    rows = query_bq(
        sql,
        {
            "user_id":
                user_id,
        },
    )

    return [

        {

            "id_topic":
                row["ID_TOPIC"],

            "label":
                row["LABEL"],

            "content_count":
                row.get(
                    "CONTENT_COUNT",
                    0,
                ),

            "universes":
                row.get(
                    "UNIVERSES",
                )
                or [],

        }

        for row in rows

    ]
