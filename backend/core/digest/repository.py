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

from core.delivery.models import (
    KnowledgeResult,
)

from core.digest.models import (
    DigestDocument,
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

TABLE_COMPANY = (
    f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_COMPANY"
)

TABLE_SOLUTION = (
    f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_SOLUTION"
)

TABLE_TOPIC = (
    f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_TOPIC"
)

# ============================================================
# CAMPAIGN MAPPING
# ============================================================

def _map_campaign(
    row,
) -> Campaign:

    return Campaign(

        id=row["ID"],

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
    Return a weekly Campaign by id.
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

def fetch_campaign_for_period(
    audience: str,
    period_start,
    period_end,
) -> Campaign | None:
    """
    Return the weekly Campaign matching one
    exact audience and period.
    """

    sql = f"""
        SELECT *

        FROM `{TABLE_CAMPAIGN}`

        WHERE AUDIENCE = @audience
          AND PERIOD_START = @period_start
          AND PERIOD_END = @period_end

        ORDER BY CREATED_AT DESC

        LIMIT 1
    """

    rows = query_bq(
        sql,
        {
            "audience":
                audience,

            "period_start":
                period_start,

            "period_end":
                period_end,
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
    Return weekly Campaign history.
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
            KnowledgeResult.model_validate(
                row["KNOWLEDGE"],
            )
        )

    document = None

    if row.get("DOCUMENT"):

        document = (
            DigestDocument.model_validate(
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
            digest.user_id,

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
                digest.knowledge.model_dump(
                    mode="json",
                )
                if digest.knowledge
                else None,

            "DOCUMENT":
                digest.document.model_dump(
                    mode="json",
                )
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
    Return a weekly Digest by id.
    """

    sql = f"""
        SELECT
            d.*

        FROM `{TABLE_DIGEST}` d

        JOIN `{TABLE_CAMPAIGN}` c
          ON c.ID = d.CAMPAIGN_ID

        WHERE d.ID = @id
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


def fetch_digest_for_period(
    user_id: str,
    period_start,
    period_end,
) -> Digest | None:
    """
    Return the weekly Digest matching one
    profile and exact period.
    """

    sql = f"""
        SELECT
            d.*

        FROM `{TABLE_DIGEST}` d

        JOIN `{TABLE_CAMPAIGN}` c
          ON c.ID = d.CAMPAIGN_ID

        WHERE d.USER_ID = @user_id
          AND c.PERIOD_START = @period_start
          AND c.PERIOD_END = @period_end

        ORDER BY
            d.GENERATED_AT DESC

        LIMIT 1
    """

    rows = query_bq(
        sql,
        {
            "user_id":
                user_id,

            "period_start":
                period_start,

            "period_end":
                period_end,
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


def fetch_digests_for_user(
    user_id: str,
) -> list[Digest]:

    sql = f"""
        SELECT
            d.*

        FROM `{TABLE_DIGEST}` d

        JOIN `{TABLE_CAMPAIGN}` c
          ON c.ID = d.CAMPAIGN_ID

        WHERE d.USER_ID = @user_id

          AND d.STATUS IN (
              "generated",
              "sent"
          )

        ORDER BY
            c.PERIOD_END DESC,
            d.GENERATED_AT DESC
    """

    rows = query_bq(
        sql,
        {
            "user_id":
                user_id,
        },
    )

    return [

        _map_digest(
            row,
        )

        for row in rows

    ]

# ============================================================
# RECENT DIGEST DOCUMENTS
# ============================================================

def fetch_recent_digest_documents(
    user_id: str,
    limit: int,
) -> list[DigestDocument]:
    """
    Return the most recent weekly Digest
    documents used by Conversation.
    """

    sql = f"""
        SELECT
            d.DOCUMENT

        FROM `{TABLE_DIGEST}` d

        JOIN `{TABLE_CAMPAIGN}` c
          ON c.ID = d.CAMPAIGN_ID

        WHERE d.USER_ID = @user_id

          AND d.STATUS IN (
              "generated",
              "sent"
          )

          AND d.DOCUMENT IS NOT NULL

        ORDER BY
            c.PERIOD_END DESC,
            d.GENERATED_AT DESC

        LIMIT @limit
    """

    rows = query_bq(
        sql,
        {
            "user_id":
                user_id,

            "limit":
                limit,
        },
    ) or []

    return [

        DigestDocument.model_validate(
            row["DOCUMENT"],
        )

        for row in rows

        if row.get(
            "DOCUMENT",
        )

    ]

def fetch_digest_history(
    user_id: str,
) -> list[dict]:

    sql = f"""
        SELECT

            d.ID,
            d.CAMPAIGN_ID,
            d.USER_ID,
            d.STATUS,
            d.TOTAL_CONTENTS,
            d.ANALYZED_CONTENTS,
            d.GENERATED_AT,
            d.SENT_AT,
            c.AUDIENCE,
            c.PERIOD_START,
            c.PERIOD_END

        FROM `{TABLE_DIGEST}` d

        JOIN `{TABLE_CAMPAIGN}` c
          ON c.ID = d.CAMPAIGN_ID

        WHERE d.USER_ID = @user_id

          AND d.STATUS IN (
              "generated",
              "sent"
          )

        ORDER BY
            c.PERIOD_END DESC,
            d.GENERATED_AT DESC
    """

    return query_bq(
        sql,
        {
            "user_id": user_id,
        },
    ) or []

# ============================================================
# DELETE DIGEST
# ============================================================

def delete_digest(
    digest_id: str,
) -> bool:
    """
    Delete one Digest and refresh its Campaign counters.

    Returns False when the Digest does not exist.
    """

    digest = fetch_digest(
        digest_id,
    )

    if digest is None:

        return False

    campaign_id = (
        digest.campaign_id
    )

    client = get_bigquery_client()

    sql = f"""
        BEGIN TRANSACTION;

        DELETE FROM `{TABLE_DIGEST}`

        WHERE ID = @digest_id;


        UPDATE `{TABLE_CAMPAIGN}` c

        SET

            DIGESTS_COUNT = (

                SELECT COUNT(*)

                FROM `{TABLE_DIGEST}` d

                WHERE
                    d.CAMPAIGN_ID = @campaign_id

            ),

            GENERATED_COUNT = (

                SELECT COUNT(*)

                FROM `{TABLE_DIGEST}` d

                WHERE
                    d.CAMPAIGN_ID = @campaign_id

                    AND d.STATUS IN (
                        "generated",
                        "sending",
                        "sent"
                    )

            ),

            SENT_COUNT = (

                SELECT COUNT(*)

                FROM `{TABLE_DIGEST}` d

                WHERE
                    d.CAMPAIGN_ID = @campaign_id

                    AND d.STATUS = "sent"

            ),

            FAILED_COUNT = (

                SELECT COUNT(*)

                FROM `{TABLE_DIGEST}` d

                WHERE
                    d.CAMPAIGN_ID = @campaign_id

                    AND d.STATUS = "failed"

            )

        WHERE
            c.ID = @campaign_id;

        COMMIT TRANSACTION;
    """

    job_config = bigquery.QueryJobConfig(

        query_parameters=[

            bigquery.ScalarQueryParameter(
                "digest_id",
                "STRING",
                digest_id,
            ),

            bigquery.ScalarQueryParameter(
                "campaign_id",
                "STRING",
                campaign_id,
            ),

        ],

    )

    client.query(

        sql,

        job_config=job_config,

    ).result()

    return True

def search_digest_history(
    query: str | None = None,
    user_id: str | None = None,
    company_id: str | None = None,
    solution_id: str | None = None,
    topic_id: str | None = None,
) -> list[dict]:
    """
    Search available Digest history.

    A Digest is always linked to a user/profile.

    Search can be performed through:
    - user / expert identity
    - company preferences
    - solution preferences
    - topic preferences
    """

    table_user = (
        f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_USER"
    )

    table_preferences = (
        f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_USER_PREFERENCES"
    )

    sql = f"""
        SELECT DISTINCT

            d.ID,
            d.CAMPAIGN_ID,
            d.USER_ID,
            d.STATUS,

            d.TOTAL_CONTENTS,
            d.ANALYZED_CONTENTS,

            d.GENERATED_AT,
            d.SENT_AT,
            c.AUDIENCE,
            c.PERIOD_START,
            c.PERIOD_END,

            u.NAME,
            u.DISPLAY_NAME,
            u.COMPANY,
            u.DESCRIPTION,
            u.PROFILE_TYPE

        FROM `{TABLE_DIGEST}` d

        JOIN `{TABLE_CAMPAIGN}` c
          ON c.ID = d.CAMPAIGN_ID

        JOIN `{table_user}` u
          ON u.ID_USER = d.USER_ID

        WHERE
            d.STATUS IN (
                "generated",
                "sent"
            )

            AND (
                @user_id IS NULL
                OR d.USER_ID = @user_id
            )

            AND (
                @query IS NULL

                OR LOWER(
                    COALESCE(
                        u.DISPLAY_NAME,
                        ""
                    )
                )
                LIKE CONCAT(
                    "%",
                    LOWER(@query),
                    "%"
                )

                OR LOWER(
                    COALESCE(
                        u.NAME,
                        ""
                    )
                )
                LIKE CONCAT(
                    "%",
                    LOWER(@query),
                    "%"
                )

                OR LOWER(
                    COALESCE(
                        u.COMPANY,
                        ""
                    )
                )
                LIKE CONCAT(
                    "%",
                    LOWER(@query),
                    "%"
                )

                OR EXISTS (

                    SELECT 1

                    FROM `{table_preferences}` p

                    LEFT JOIN `{TABLE_COMPANY}` co
                      ON p.TYPE = "COMPANY"
                     AND p.VALUE_ID = co.ID_COMPANY

                    LEFT JOIN `{TABLE_SOLUTION}` s
                      ON p.TYPE = "SOLUTION"
                     AND p.VALUE_ID = s.ID_SOLUTION

                    LEFT JOIN `{TABLE_TOPIC}` t
                      ON p.TYPE = "TOPIC"
                     AND p.VALUE_ID = t.ID_TOPIC

                    WHERE
                        p.ID_USER = d.USER_ID

                        AND (

                            LOWER(
                                COALESCE(
                                    co.NAME,
                                    ""
                                )
                            )
                            LIKE CONCAT(
                                "%",
                                LOWER(@query),
                                "%"
                            )

                            OR LOWER(
                                COALESCE(
                                    s.NAME,
                                    ""
                                )
                            )
                            LIKE CONCAT(
                                "%",
                                LOWER(@query),
                                "%"
                            )

                            OR LOWER(
                                COALESCE(
                                    t.LABEL,
                                    ""
                                )
                            )
                            LIKE CONCAT(
                                "%",
                                LOWER(@query),
                                "%"
                            )

                        )

                )

            )

            AND (
                @company_id IS NULL

                OR EXISTS (

                    SELECT 1

                    FROM `{table_preferences}` p

                    WHERE
                        p.ID_USER = d.USER_ID
                        AND p.TYPE = "COMPANY"
                        AND p.VALUE_ID = @company_id

                )

            )

            AND (
                @solution_id IS NULL

                OR EXISTS (

                    SELECT 1

                    FROM `{table_preferences}` p

                    WHERE
                        p.ID_USER = d.USER_ID
                        AND p.TYPE = "SOLUTION"
                        AND p.VALUE_ID = @solution_id

                )

            )

            AND (
                @topic_id IS NULL

                OR EXISTS (

                    SELECT 1

                    FROM `{table_preferences}` p

                    WHERE
                        p.ID_USER = d.USER_ID
                        AND p.TYPE = "TOPIC"
                        AND p.VALUE_ID = @topic_id

                )

            )

        ORDER BY
            c.PERIOD_END DESC,
            d.GENERATED_AT DESC
    """

    return query_bq(
        sql,
        {
            "query":
                query.strip()
                if query
                else None,

            "user_id":
                user_id,

            "company_id":
                company_id,

            "solution_id":
                solution_id,

            "topic_id":
                topic_id,
        },
    ) or []


# ============================================================
# ADMIN DIGEST SEARCH
# ============================================================

def search_admin_digest_history(
    query: str | None = None,
    audience: str | None = None,
    status: str | None = None,
    campaign_id: str | None = None,
    period_start: str | None = None,
    period_end: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> dict:
    """
    Search every Digest available in the admin.

    Results include all Digest statuses and can be
    filtered by recipient, audience, status, campaign
    and period.
    """

    table_user = (
        f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_USER"
    )

    safe_limit = min(
        max(
            limit,
            1,
        ),
        200,
    )

    safe_offset = max(
        offset,
        0,
    )

    sql = f"""
        SELECT

            d.ID,
            d.CAMPAIGN_ID,
            d.USER_ID,
            d.STATUS,

            d.TOTAL_CONTENTS,
            d.ANALYZED_CONTENTS,

            d.GENERATED_AT,
            d.SENT_AT,
            d.ERROR,

            c.AUDIENCE,
            c.PERIOD_START,
            c.PERIOD_END,

            u.NAME,
            u.DISPLAY_NAME,
            u.EMAIL,
            u.COMPANY,
            u.DESCRIPTION,
            u.PROFILE_TYPE,

            COUNT(*) OVER() AS TOTAL_COUNT

        FROM `{TABLE_DIGEST}` d

        JOIN `{TABLE_CAMPAIGN}` c
          ON c.ID = d.CAMPAIGN_ID

        LEFT JOIN `{table_user}` u
          ON u.ID_USER = d.USER_ID

        WHERE

            (
                @query IS NULL

                OR LOWER(
                    COALESCE(
                        u.DISPLAY_NAME,
                        ""
                    )
                )
                LIKE CONCAT(
                    "%",
                    LOWER(@query),
                    "%"
                )

                OR LOWER(
                    COALESCE(
                        u.NAME,
                        ""
                    )
                )
                LIKE CONCAT(
                    "%",
                    LOWER(@query),
                    "%"
                )

                OR LOWER(
                    COALESCE(
                        u.EMAIL,
                        ""
                    )
                )
                LIKE CONCAT(
                    "%",
                    LOWER(@query),
                    "%"
                )

                OR LOWER(
                    COALESCE(
                        u.COMPANY,
                        ""
                    )
                )
                LIKE CONCAT(
                    "%",
                    LOWER(@query),
                    "%"
                )

            )

            AND (
                @audience IS NULL
                OR c.AUDIENCE = @audience
            )

            AND (
                @status IS NULL
                OR d.STATUS = @status
            )

            AND (
                @campaign_id IS NULL
                OR d.CAMPAIGN_ID = @campaign_id
            )

            AND (
                @period_start IS NULL
                OR c.PERIOD_END >= @period_start
            )

            AND (
                @period_end IS NULL
                OR c.PERIOD_START <= @period_end
            )

        ORDER BY
            c.PERIOD_END DESC,
            d.GENERATED_AT DESC,
            u.DISPLAY_NAME ASC,
            u.NAME ASC

        LIMIT @limit
        OFFSET @offset
    """

    rows = query_bq(
        sql,
        {
            "query":
                query.strip()
                if query
                else None,

            "audience":
                audience,

            "status":
                status,

            "campaign_id":
                campaign_id,

            "period_start":
                period_start,

            "period_end":
                period_end,

            "limit":
                safe_limit,

            "offset":
                safe_offset,
        },
    ) or []

    total = (
        int(
            rows[0].get(
                "TOTAL_COUNT",
                0,
            )
        )
        if rows
        else 0
    )

    items = []

    for row in rows:

        items.append({

            "id":
                row["ID"],

            "campaign_id":
                row["CAMPAIGN_ID"],

            "user_id":
                row["USER_ID"],

            "status":
                row["STATUS"],

            "total_contents":
                row.get(
                    "TOTAL_CONTENTS",
                ) or 0,

            "analyzed_contents":
                row.get(
                    "ANALYZED_CONTENTS",
                ) or 0,

            "generated_at":
                row.get(
                    "GENERATED_AT",
                ),

            "sent_at":
                row.get(
                    "SENT_AT",
                ),

            "error":
                row.get(
                    "ERROR",
                ),

            "audience":
                row["AUDIENCE"],

            "period_start":
                row["PERIOD_START"],

            "period_end":
                row["PERIOD_END"],

            "name":
                row.get(
                    "NAME",
                ),

            "display_name":
                row.get(
                    "DISPLAY_NAME",
                ),

            "email":
                row.get(
                    "EMAIL",
                ),

            "company":
                row.get(
                    "COMPANY",
                ),

            "description":
                row.get(
                    "DESCRIPTION",
                ),

            "profile_type":
                row.get(
                    "PROFILE_TYPE",
                ),

        })

    return {

        "items":
            items,

        "total":
            total,

        "limit":
            safe_limit,

        "offset":
            safe_offset,

    }
