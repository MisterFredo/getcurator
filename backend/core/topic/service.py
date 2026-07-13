# ============================================================
# IMPORTS
# ============================================================

import uuid

from datetime import datetime

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

from api.topic.models import (
    TopicCreate,
    TopicUpdate,
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


# ============================================================
# CREATE TOPIC
# ============================================================
# ============================================================
# CREATE
# ============================================================

def create_topic(
    data: TopicCreate,
) -> str:

    topic_id = str(
        uuid.uuid4()
    )

    now = (
        datetime.utcnow()
        .isoformat()
    )

    row = [{

        "ID_TOPIC": topic_id,

        "LABEL": data.label,

        "DESCRIPTION": (
            data.description
            or None
        ),

        "MEDIA_SQUARE_ID": None,

        "MEDIA_RECTANGLE_ID": None,

        "SEO_TITLE": (
            data.seo_title
            or None
        ),

        "SEO_DESCRIPTION": (
            data.seo_description
            or None
        ),

        "CREATED_AT": now,

        "UPDATED_AT": now,

        "IS_ACTIVE": True,

    }]

    client = (
        get_bigquery_client()
    )

    client.load_table_from_json(

        row,

        TABLE_TOPIC,

        job_config=(
            bigquery.LoadJobConfig(
                write_disposition="WRITE_APPEND"
            )
        ),

    ).result()

    if data.universe_ids:

        rows = [

            {

                "ID_TOPIC": topic_id,

                "ID_UNIVERSE": universe_id,

                "CREATED_AT": now,

            }

            for universe_id in data.universe_ids

        ]

        client.load_table_from_json(

            rows,

            TABLE_TOPIC_UNIVERSE,

            job_config=(
                bigquery.LoadJobConfig(
                    write_disposition="WRITE_APPEND"
                )
            ),

        ).result()

    return topic_id


# ============================================================
# LIST TOPICS
# ============================================================
# ============================================================
# LIST
# ============================================================

def list_topics():

    sql = f"""
    SELECT
        t.ID_TOPIC,
        t.LABEL,
        ARRAY_AGG(
            STRUCT(
                tu.ID_UNIVERSE,
                u.LABEL
            )
            IGNORE NULLS
        ) AS UNIVERSES
    FROM `{TABLE_TOPIC}` t
    LEFT JOIN `{TABLE_TOPIC_UNIVERSE}` tu
        ON tu.ID_TOPIC = t.ID_TOPIC
    LEFT JOIN `{BQ_PROJECT}.{BQ_DATASET}.RATECARD_UNIVERSE` u
        ON u.ID_UNIVERSE = tu.ID_UNIVERSE
    WHERE COALESCE(t.IS_ACTIVE, TRUE) = TRUE
    GROUP BY
        t.ID_TOPIC,
        t.LABEL
    ORDER BY UPPER(t.LABEL)
    """

    rows = query_bq(sql)

    return [
        {
            "id_topic": r["ID_TOPIC"],
            "label": r["LABEL"],
            "universes": [
                {
                    "id_universe": u["ID_UNIVERSE"],
                    "label": u["LABEL"],
                }
                for u in (r.get("UNIVERSES") or [])
                if u.get("ID_UNIVERSE")
            ],
        }
        for r in rows
    ]


# ============================================================
# LIST CURATOR
# ============================================================

def list_topics_for_user(user_id: str):

    sql = f"""
    SELECT
        t.ID_TOPIC,
        t.LABEL
    FROM `{TABLE_TOPIC}` t
    JOIN `{TABLE_TOPIC_UNIVERSE}` tu
        ON tu.ID_TOPIC = t.ID_TOPIC
    JOIN `{TABLE_USER_UNIVERSE}` uu
        ON uu.ID_UNIVERSE = tu.ID_UNIVERSE
    WHERE
        t.IS_ACTIVE = TRUE
        AND uu.ID_USER = @user_id
    GROUP BY
        t.ID_TOPIC,
        t.LABEL
    ORDER BY UPPER(t.LABEL)
    """

    rows = query_bq(
        sql,
        {
            "user_id": user_id,
        },
    )

    return [
        {
            "id_topic": r["ID_TOPIC"],
            "label": r["LABEL"],
        }
        for r in rows
    ]

# ============================================================
# GET ONE TOPIC
# ============================================================
def get_topic(topic_id: str):

    sql = f"""
        SELECT
            t.ID_TOPIC,
            t.LABEL,
            t.DESCRIPTION,
            t.SEO_TITLE,
            t.SEO_DESCRIPTION,
            t.INSIGHT_FREQUENCY,
            t.MEDIA_SQUARE_ID,
            t.MEDIA_RECTANGLE_ID,
            t.IS_ACTIVE,
            t.CREATED_AT,
            t.UPDATED_AT,

            ARRAY_AGG(
                STRUCT(
                    u.ID_UNIVERSE AS ID_UNIVERSE,
                    u2.LABEL AS LABEL
                )
            ) AS UNIVERS

        FROM `{TABLE_TOPIC}` t

        LEFT JOIN `{TABLE_TOPIC_UNIVERSE}` u
          ON u.ID_TOPIC = t.ID_TOPIC

        LEFT JOIN `{BQ_PROJECT}.{BQ_DATASET}.RATECARD_UNIVERSE` u2
          ON u.ID_UNIVERSE = u2.ID_UNIVERSE

        WHERE t.ID_TOPIC = @id

        GROUP BY
            t.ID_TOPIC,
            t.LABEL,
            t.DESCRIPTION,
            t.SEO_TITLE,
            t.SEO_DESCRIPTION,
            t.INSIGHT_FREQUENCY,
            t.MEDIA_SQUARE_ID,
            t.MEDIA_RECTANGLE_ID,
            t.IS_ACTIVE,
            t.CREATED_AT,
            t.UPDATED_AT
    """

    rows = query_bq(sql, {"id": topic_id})

    if not rows:
        return None

    r = rows[0]

    return {
        "id_topic": r["ID_TOPIC"],
        "label": r["LABEL"],
        "description": r.get("DESCRIPTION"),
        "seo_title": r.get("SEO_TITLE"),
        "seo_description": r.get("SEO_DESCRIPTION"),
        "insight_frequency": r.get("INSIGHT_FREQUENCY"),
        "is_active": r.get("IS_ACTIVE", True),

        "universes": [
            {
                "id_universe": u["ID_UNIVERSE"],
                "label": u["LABEL"],
            }
            for u in (r.get("UNIVERS") or [])
            if u["ID_UNIVERSE"]
        ],

        "created_at": r.get("CREATED_AT"),
        "updated_at": r.get("UPDATED_AT"),
    }

# ============================================================
# UPDATE TOPIC
# ============================================================
# ============================================================
# UPDATE
# ============================================================

def update_topic(
    id_topic: str,
    data: TopicUpdate,
) -> bool:

    values = data.dict(
        exclude_unset=True
    )

    if not values:
        return False

    now = (
        datetime.utcnow()
        .isoformat()
    )

    mapping = {
        "label": "LABEL",
        "description": "DESCRIPTION",
        "seo_title": "SEO_TITLE",
        "seo_description": "SEO_DESCRIPTION",
        "media_square_id": "MEDIA_SQUARE_ID",
        "media_rectangle_id": "MEDIA_RECTANGLE_ID",
        "is_active": "IS_ACTIVE",
    }

    bq_values = {
        mapping[k]: v
        for k, v in values.items()
        if k in mapping
    }

    if bq_values:

        bq_values["UPDATED_AT"] = now

        update_bq(
            table=TABLE_TOPIC,
            fields=bq_values,
            where={
                "ID_TOPIC": id_topic,
            },
        )

    if "universe_ids" in values:

        client = get_bigquery_client()

        query_bq(
            f"""
            DELETE FROM `{TABLE_TOPIC_UNIVERSE}`
            WHERE ID_TOPIC = @id
            """,
            {
                "id": id_topic,
            },
        )

        if values["universe_ids"]:

            rows = [
                {
                    "ID_TOPIC": id_topic,
                    "ID_UNIVERSE": universe_id,
                    "CREATED_AT": now,
                }
                for universe_id in values["universe_ids"]
            ]

            client.load_table_from_json(
                rows,
                TABLE_TOPIC_UNIVERSE,
                job_config=bigquery.LoadJobConfig(
                    write_disposition="WRITE_APPEND"
                ),
            ).result()

    return True


# ============================================================
# DELETE
# ============================================================

def delete_topic(
    id_topic: str,
) -> bool:

    existing = query_bq(
        f"""
        SELECT ID_TOPIC
        FROM `{TABLE_TOPIC}`
        WHERE ID_TOPIC = @id
        """,
        {
            "id": id_topic,
        },
    )

    if not existing:
        return False

    return update_bq(
        table=TABLE_TOPIC,
        fields={
            "IS_ACTIVE": False,
            "UPDATED_AT": (
                datetime.utcnow()
                .isoformat()
            ),
        },
        where={
            "ID_TOPIC": id_topic,
        },
    )
