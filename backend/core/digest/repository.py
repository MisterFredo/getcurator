import json

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
    Campaign,
    Digest,
)

# ============================================================
# TABLES
# ============================================================

TABLE_CAMPAIGN = (
    f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_CAMPAIGN"
)

TABLE_DIGEST = (
    f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_DIGEST"
)

# ============================================================
# CAMPAIGN MAPPING
# ============================================================

def _map_campaign(
    row,
) -> Campaign:

    return Campaign(

        id=row["ID"],

        frequency=row["FREQUENCY"],

        audience=row["AUDIENCE"],

        period_start=row["PERIOD_START"],

        period_end=row["PERIOD_END"],

        status=row["STATUS"],

        digests_count=row["DIGESTS_COUNT"],

        generated_count=row["GENERATED_COUNT"],

        sent_count=row["SENT_COUNT"],

        failed_count=row["FAILED_COUNT"],

        created_at=row["CREATED_AT"],

        completed_at=row.get(
            "COMPLETED_AT",
        ),

    )

# ============================================================
# CAMPAIGN
# ============================================================

def insert_campaign(
    campaign: Campaign,
) -> Campaign:
    """
    Persist a new Campaign.
    """

    client = get_bigquery_client()

    row = [{

        "ID": campaign.id,

        "FREQUENCY": campaign.frequency,

        "AUDIENCE": campaign.audience,

        "PERIOD_START":
            campaign.period_start.isoformat(),

        "PERIOD_END":
            campaign.period_end.isoformat(),

        "STATUS":
            campaign.status,

        "DIGESTS_COUNT":
            campaign.digests_count,

        "GENERATED_COUNT":
            campaign.generated_count,

        "SENT_COUNT":
            campaign.sent_count,

        "FAILED_COUNT":
            campaign.failed_count,

        "CREATED_AT":
            campaign.created_at.isoformat(),

        "COMPLETED_AT":
            campaign.completed_at.isoformat()
            if campaign.completed_at
            else None,

    }]

    client.load_table_from_json(

        row,

        TABLE_CAMPAIGN,

        job_config=bigquery.LoadJobConfig(

            write_disposition="WRITE_APPEND",

        ),

    ).result()

    return campaign


def update_campaign(
    campaign: Campaign,
) -> Campaign:
    """
    Update an existing Campaign.
    """

    update_bq(

        table=TABLE_CAMPAIGN,

        where={

            "ID": campaign.id,

        },

        fields={

            "STATUS":
                campaign.status,

            "DIGESTS_COUNT":
                campaign.digests_count,

            "GENERATED_COUNT":
                campaign.generated_count,

            "SENT_COUNT":
                campaign.sent_count,

            "FAILED_COUNT":
                campaign.failed_count,

            "COMPLETED_AT":
                campaign.completed_at,

        },

    )

    return campaign


def fetch_campaign(
    campaign_id: str,
) -> Campaign | None:
    """
    Return a Campaign by id.
    """

    sql = f"""
        SELECT *

        FROM `{TABLE_CAMPAIGN}`

        WHERE ID = @id

        LIMIT 1
    """

    rows = query_bq(

        sql,

        {

            "id": campaign_id,

        },

    )

    if not rows:

        return None

    return _map_campaign(

        rows[0],

    )


def fetch_campaigns(
) -> list[Campaign]:
    """
    Return Campaign history.
    """

    sql = f"""
        SELECT *

        FROM `{TABLE_CAMPAIGN}`

        ORDER BY CREATED_AT DESC
    """

    rows = query_bq(
        sql,
    )

    return [

        _map_campaign(
            row,
        )

        for row in rows

    ]


# ============================================================
# DIGEST MAPPING
# ============================================================

def _map_digest(
    row,
) -> Digest:

    knowledge = None

    if row.get("KNOWLEDGE"):

        knowledge = (
            KnowledgeResult.model_validate_json(
                row["KNOWLEDGE"],
            )
        )

    document = None

    if row.get("DOCUMENT"):

        document = (
            DigestDocument.model_validate_json(
                row["DOCUMENT"],
            )
        )

    return Digest(

        id=row["ID"],

        campaign_id=row["CAMPAIGN_ID"],

        user_id=row["USER_ID"],

        status=row["STATUS"],

        total_contents=row["TOTAL_CONTENTS"],

        analyzed_contents=row["ANALYZED_CONTENTS"],

        knowledge=knowledge,

        document=document,

        generated_at=row.get(
            "GENERATED_AT",
        ),

        sent_at=row.get(
            "SENT_AT",
        ),

        error=row.get(
            "ERROR",
        ),

    )


# ============================================================
# DIGEST
# ============================================================

def insert_digest(
    digest: Digest,
) -> Digest:
    """
    Persist a Digest.
    """

    client = get_bigquery_client()

    row = [{

        "ID":
            digest.id,

        "CAMPAIGN_ID":
            digest.campaign_id,

        "USER_ID":
            digest.request.user_id,

        "STATUS":
            digest.status,

        "PERIOD_START":
            digest.request.period_start.isoformat(),

        "PERIOD_END":
            digest.request.period_end.isoformat(),

        "TOTAL_CONTENTS":
            digest.total_contents,

        "ANALYZED_CONTENTS":
            digest.analyzed_contents,

        "KNOWLEDGE":
            digest.knowledge.model_dump_json()
            if digest.knowledge
            else None,

        "DOCUMENT":
            digest.document.model_dump_json()
            if digest.document
            else None,

        "GENERATED_AT":
            digest.generated_at.isoformat()
            if digest.generated_at
            else None,

        "SENT_AT":
            digest.sent_at.isoformat()
            if digest.sent_at
            else None,

        "ERROR":
            digest.error,

    }]

    client.load_table_from_json(

        row,

        TABLE_DIGEST,

        job_config=bigquery.LoadJobConfig(

            write_disposition="WRITE_APPEND",

        ),

    ).result()

    return digest


def update_digest(
    digest: Digest,
) -> Digest:
    """
    Update an existing Digest.
    """

    update_bq(

        table=TABLE_DIGEST,

        where={

            "ID": digest.id,

        },

        fields={

            "STATUS":
                digest.status,

            "TOTAL_CONTENTS":
                digest.total_contents,

            "ANALYZED_CONTENTS":
                digest.analyzed_contents,

            "KNOWLEDGE":
                digest.knowledge.model_dump_json()
                if digest.knowledge
                else None,

            "DOCUMENT":
                digest.document.model_dump_json()
                if digest.document
                else None,

            "GENERATED_AT":
                digest.generated_at,

            "SENT_AT":
                digest.sent_at,

            "ERROR":
                digest.error,

        },

    )

    return digest


def fetch_digest(
    digest_id: str,
) -> Digest | None:
    """
    Return a Digest by id.
    """

    sql = f"""
        SELECT *

        FROM `{TABLE_DIGEST}`

        WHERE ID = @id

        LIMIT 1
    """

    rows = query_bq(

        sql,

        {

            "id": digest_id,

        },

    )

    if not rows:

        return None

    return _map_digest(

        rows[0],

    )


def fetch_digests(
    campaign_id: str,
) -> list[Digest]:
    """
    Return all Digests belonging to a Campaign.
    """

    sql = f"""
        SELECT *

        FROM `{TABLE_DIGEST}`

        WHERE CAMPAIGN_ID = @campaign_id

        ORDER BY GENERATED_AT DESC
    """

    rows = query_bq(

        sql,

        {

            "campaign_id": campaign_id,

        },

    )

    return [

        _map_digest(
            row,
        )

        for row in rows

    ]
