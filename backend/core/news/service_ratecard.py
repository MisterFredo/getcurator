import uuid
from datetime import datetime, timezone
from typing import Optional, List
from google.cloud import bigquery

from config import BQ_PROJECT, BQ_DATASET
from utils.bigquery_utils import (
    query_bq,
    insert_bq,
    get_bigquery_client,
    update_bq,
)

from api.news.models import NewsCreate, NewsUpdate


# ============================================================
# TABLES
# ============================================================
TABLE_NEWS = f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_NEWS"
TABLE_NEWS_TOPIC = f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_NEWS_TOPIC"
TABLE_NEWS_PERSON = f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_NEWS_PERSON"

TABLE_COMPANY = f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_COMPANY"
TABLE_TOPIC = f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_TOPIC"
TABLE_PERSON = f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_PERSON"
TABLE_NEWS_LINKEDIN_POST = f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_NEWS_LINKEDIN_POST"

TABLE_NEWS_CONCEPT = f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_NEWS_CONCEPT"
TABLE_NEWS_SOLUTION = f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_NEWS_SOLUTION"
TABLE_CONCEPT = f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_CONCEPT"
TABLE_SOLUTION = f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_SOLUTION"


# ============================================================
# CREATE NEWS / BRÈVE
# ============================================================

def create_news(
    data: NewsCreate,
) -> str:

    # ============================================================
    # VALIDATION
    # ============================================================

    if not data.id_company:
        raise ValueError(
            "id_company obligatoire"
        )

    if not data.title or not data.title.strip():
        raise ValueError(
            "title obligatoire"
        )

    # ============================================================
    # PREPARE
    # ============================================================

    news_id = str(uuid.uuid4())

    now = datetime.utcnow().isoformat()

    # ============================================================
    # INSERT
    # ============================================================

    row = [{

        "ID_NEWS": news_id,

        "STATUS": "DRAFT",

        "IS_ACTIVE": True,

        "NEWS_TYPE": data.news_type,

        "ID_COMPANY": data.id_company,

        "TITLE": data.title.strip(),

        "EXCERPT": data.excerpt,

        "BODY": data.body,

        "SOURCE_URL": data.source_url,

        "AUTHOR": data.author,

        "PUBLISHED_AT": None,

        "CREATED_AT": now,

        "UPDATED_AT": now,

    }]

    client = get_bigquery_client()

    client.load_table_from_json(
        row,
        TABLE_NEWS,
        job_config=bigquery.LoadJobConfig(
            write_disposition="WRITE_APPEND",
        ),
    ).result()

    # ============================================================
    # DONE
    # ============================================================

    return news_id

def get_news(
    id_news: str,
):

    rows = query_bq(
        f"""
        SELECT

            n.ID_NEWS,

            n.STATUS,

            n.NEWS_TYPE,

            n.TITLE,
            n.EXCERPT,
            n.BODY,

            n.SOURCE_URL,
            n.AUTHOR,

            n.PUBLISHED_AT,
            n.CREATED_AT,
            n.UPDATED_AT,

            c.ID_COMPANY,
            c.NAME AS COMPANY_NAME,
            c.IS_PARTNER

        FROM `{TABLE_NEWS}` n

        JOIN `{TABLE_COMPANY}` c
          ON n.ID_COMPANY = c.ID_COMPANY

        WHERE n.ID_NEWS = @id

        LIMIT 1
        """,
        {"id": id_news},
    )

    if not rows:
        return None

    r = rows[0]

    return {

        "id_news": r["ID_NEWS"],

        "status": r["STATUS"],

        "news_type": r["NEWS_TYPE"],

        "title": r["TITLE"],

        "excerpt": r["EXCERPT"],

        "body": r["BODY"],

        "source_url": r["SOURCE_URL"],

        "author": r["AUTHOR"],

        "published_at": (
            r["PUBLISHED_AT"].isoformat()
            if r["PUBLISHED_AT"]
            else None
        ),

        "created_at": (
            r["CREATED_AT"].isoformat()
            if r["CREATED_AT"]
            else None
        ),

        "updated_at": (
            r["UPDATED_AT"].isoformat()
            if r["UPDATED_AT"]
            else None
        ),

        "company": {

            "id_company": r["ID_COMPANY"],

            "name": r["COMPANY_NAME"],

            "is_partner": bool(
                r["IS_PARTNER"]
            ),

        },

    }

# ============================================================
# LIST NEWS / BRÈVES (PUBLIC)
# ============================================================
# ============================================================
# LIST NEWS (PUBLIC)
# ============================================================

def list_news():

    sql = f"""
        SELECT

            n.ID_NEWS,
            n.STATUS,
            n.NEWS_TYPE,

            n.TITLE,
            n.EXCERPT,
            n.BODY,

            n.SOURCE_URL,
            n.AUTHOR,

            n.PUBLISHED_AT,
            n.CREATED_AT,

            c.ID_COMPANY,
            c.NAME AS COMPANY_NAME,
            c.MEDIA_LOGO_RECTANGLE_ID,
            c.IS_PARTNER

        FROM `{TABLE_NEWS}` n

        JOIN `{TABLE_COMPANY}` c
          ON n.ID_COMPANY = c.ID_COMPANY

        WHERE
            n.STATUS = 'PUBLISHED'
            AND n.PUBLISHED_AT IS NOT NULL
            AND n.PUBLISHED_AT <= CURRENT_TIMESTAMP()

        ORDER BY
            n.PUBLISHED_AT DESC
    """

    return query_bq(sql)


# ============================================================
# NEWS TYPES (RÉFÉRENTIEL ÉDITORIAL)
# ============================================================

def list_news_types():

    return query_bq(
        f"""
        SELECT
            CODE,
            LABEL
        FROM `{BQ_PROJECT}.{BQ_DATASET}.RATECARD_NEWS_TYPE`
        WHERE IS_ACTIVE = TRUE
        ORDER BY LABEL
        """
    )


# ============================================================
# UPDATE NEWS / BRÈVE
# ============================================================

def update_news(
    id_news: str,
    data: NewsUpdate,
):

    values = data.dict(
        exclude_unset=True,
    )

    if not values:
        return True

    field_map = {

        "news_type": "NEWS_TYPE",

        "id_company": "ID_COMPANY",

        "title": "TITLE",

        "excerpt": "EXCERPT",

        "body": "BODY",

        "source_url": "SOURCE_URL",

        "author": "AUTHOR",

    }

    fields = {}

    for key, value in values.items():

        column = field_map.get(key)

        if column:
            fields[column] = value

    if not fields:
        return True

    fields["UPDATED_AT"] = (
        datetime.utcnow().isoformat()
    )

    update_bq(
        table=TABLE_NEWS,
        fields=fields,
        where={
            "ID_NEWS": id_news,
        },
    )

    return True


# ============================================================
# ARCHIVE / DELETE
# ============================================================
def archive_news(id_news: str):
    update_bq(
        table=TABLE_NEWS,
        fields={"STATUS": "ARCHIVED"},
        where={"ID_NEWS": id_news},
    )
    return True

def delete_news(
    news_id: str,
):

    client = get_bigquery_client()

    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter(
                "id",
                "STRING",
                news_id,
            )
        ]
    )

    client.query(
        f"""
        DELETE FROM `{TABLE_NEWS_LINKEDIN_POST}`
        WHERE ID_NEWS = @id
        """,
        job_config=job_config,
    ).result()

    client.query(
        f"""
        DELETE FROM `{TABLE_NEWS}`
        WHERE ID_NEWS = @id
        """,
        job_config=job_config,
    ).result()

    return True


# ============================================================
# PUBLISH
# ============================================================

def publish_news(
    id_news: str,
    published_at: Optional[str] = None,
):

    rows = query_bq(
        f"""
        SELECT
            EXCERPT
        FROM `{TABLE_NEWS}`
        WHERE ID_NEWS = @id
        LIMIT 1
        """,
        {"id": id_news},
    )

    if not rows:
        raise ValueError(
            "News introuvable"
        )

    if not rows[0]["EXCERPT"]:
        raise ValueError(
            "Un excerpt est requis pour publier"
        )

    now = datetime.now(
        timezone.utc
    )

    if published_at:

        publish_date = (
            datetime.fromisoformat(
                published_at
            )
            if isinstance(
                published_at,
                str,
            )
            else published_at
        )

        if publish_date.tzinfo is None:
            publish_date = publish_date.replace(
                tzinfo=timezone.utc,
            )

    else:

        publish_date = now

    status = (
        "PUBLISHED"
        if publish_date <= now
        else "SCHEDULED"
    )

    update_bq(
        table=TABLE_NEWS,
        fields={
            "STATUS": status,
            "PUBLISHED_AT": publish_date.isoformat(),
            "UPDATED_AT": now.isoformat(),
        },
        where={
            "ID_NEWS": id_news,
        },
    )

    return status


# ============================================================
# SEARCH SIGNAUX — FLUX UNIQUEMENT
# ============================================================

def search_breves_public(
    topics: Optional[List[str]] = None,
    news_types: Optional[List[str]] = None,
    companies: Optional[List[str]] = None,
    limit: int = 20,
    cursor: Optional[str] = None,
):
    """
    Retourne uniquement :
    - le flux principal (items)
    - les actualités partenaires (sponsorised)

    Aucun calcul de stats ici.
    """

    params = {"limit": limit}
    where_clauses = ["status = 'PUBLISHED'"]

    # =====================================================
    # FILTRES
    # =====================================================

    if topics:
        where_clauses.append(
            """
            EXISTS (
                SELECT 1
                FROM UNNEST(topics) t
                WHERE t.id_topic IN UNNEST(@topics)
            )
            """
        )
        params["topics"] = topics

    if news_types:
        where_clauses.append("news_type IN UNNEST(@news_types)")
        params["news_types"] = news_types

    if companies:
        where_clauses.append("id_company IN UNNEST(@companies)")
        params["companies"] = companies

    if cursor:
        where_clauses.append("published_at < @cursor")
        params["cursor"] = cursor

    where_sql = " AND ".join(where_clauses)

    # =====================================================
    # ITEMS
    # =====================================================

    sql_items = f"""
        SELECT
            id_news,
            title,
            excerpt,
            published_at,
            news_type,
            news_kind,
            id_company,
            company_name,
            is_partner,
            topics
        FROM `{BQ_PROJECT}.{BQ_DATASET}.V_NEWS_ENRICHED`
        WHERE {where_sql}
        ORDER BY published_at DESC
        LIMIT @limit
    """

    rows = query_bq(sql_items, params)

    items = [
        {
            "id": r.get("id_news"),
            "title": r.get("title"),
            "excerpt": r.get("excerpt"),
            "published_at": r.get("published_at"),
            "news_type": r.get("news_type"),
            "news_kind": r.get("news_kind"),  # 🔑 IMPORTANT
            "company": {
                "id_company": r.get("id_company"),
                "name": r.get("company_name"),
                "is_partner": bool(r.get("is_partner")),
            },
            "topics": r.get("topics", []) or [],
        }
        for r in rows
    ]

    # =====================================================
    # SPONSORISED (PARTENAIRES UNIQUEMENT)
    # =====================================================

    sql_sponsorised = f"""
        SELECT
            id_news,
            title,
            excerpt,
            published_at,
            news_type,
            news_kind,
            id_company,
            company_name,
            is_partner,
            topics
        FROM `{BQ_PROJECT}.{BQ_DATASET}.V_NEWS_ENRICHED`
        WHERE {where_sql}
          AND is_partner = TRUE
        ORDER BY published_at DESC
        LIMIT 3
    """

    sponsor_rows = query_bq(sql_sponsorised, params)

    sponsorised = [
        {
            "id": r.get("id_news"),
            "title": r.get("title"),
            "excerpt": r.get("excerpt"),
            "published_at": r.get("published_at"),
            "news_type": r.get("news_type"),
            "news_kind": r.get("news_kind"),  # 🔑 IMPORTANT
            "company": {
                "id_company": r.get("id_company"),
                "name": r.get("company_name"),
                "is_partner": True,
            },
            "topics": r.get("topics", []) or [],
        }
        for r in sponsor_rows
    ]

    return {
        "items": items,
        "sponsorised": sponsorised,
    }



# ============================================================
# SIGNAUX STATS — STATS UNIQUEMENT
# ============================================================

def get_breves_stats_public():

    # =====================================================
    # GLOBAL
    # =====================================================

    global_rows = query_bq(f"""
        SELECT *
        FROM `{BQ_PROJECT}.{BQ_DATASET}.V_NEWS_STATS_GLOBAL`
    """)

    if global_rows:
        g = global_rows[0]
        total_count = g.get("TOTAL", 0) or 0
        last_7 = g.get("LAST_7_DAYS", 0) or 0
        last_30 = g.get("LAST_30_DAYS", 0) or 0
    else:
        total_count = 0
        last_7 = 0
        last_30 = 0

    # =====================================================
    # TYPES
    # =====================================================

    types_rows = query_bq(f"""
        SELECT *
        FROM `{BQ_PROJECT}.{BQ_DATASET}.V_NEWS_STATS_TYPE`
        ORDER BY TOTAL DESC
    """)

    types_stats = [
        {
            "news_type": r.get("NEWS_TYPE"),
            "total": r.get("TOTAL", 0) or 0,
            "last_7_days": r.get("LAST_7_DAYS", 0) or 0,
            "last_30_days": r.get("LAST_30_DAYS", 0) or 0,
        }
        for r in types_rows
    ]

    # =====================================================
    # TOPICS
    # =====================================================

    topics_rows = query_bq(f"""
        SELECT *
        FROM `{BQ_PROJECT}.{BQ_DATASET}.V_NEWS_STATS_TOPIC`
        ORDER BY TOTAL DESC
    """)

    topics_stats = [
        {
            "id_topic": r.get("ID_TOPIC"),
            "label": r.get("LABEL"),
            "total": r.get("TOTAL", 0) or 0,
            "last_7_days": r.get("LAST_7_DAYS", 0) or 0,
            "last_30_days": r.get("LAST_30_DAYS", 0) or 0,
        }
        for r in topics_rows
        if r.get("ID_TOPIC") and r.get("LABEL")
    ]

    # =====================================================
    # COMPANIES (NEWS + CONTENT MERGE)
    # =====================================================

    # --- NEWS ---
    news_rows = query_bq(f"""
        SELECT *
        FROM `{BQ_PROJECT}.{BQ_DATASET}.V_NEWS_STATS_COMPANY`
    """)

    # --- CONTENT (analyses) ---
    content_rows = query_bq(f"""
        SELECT *
        FROM `{BQ_PROJECT}.{BQ_DATASET}.V_CONTENT_STATS_COMPANY`
    """)

    # --- index ---
    news_map = {
        r.get("ID_COMPANY"): r
        for r in news_rows
        if r.get("ID_COMPANY")
    }

    content_map = {
        r.get("ID_COMPANY"): r
        for r in content_rows
        if r.get("ID_COMPANY")
    }

    # --- union des companies ---
    all_company_ids = set(news_map.keys()) | set(content_map.keys())

    top_companies = []

    for company_id in all_company_ids:

        news = news_map.get(company_id, {})
        content = content_map.get(company_id, {})

        name = news.get("NAME") or content.get("NAME")

        if not name:
            continue

        total_news = news.get("TOTAL", 0) or 0
        total_content = content.get("TOTAL", 0) or 0

        last7_news = news.get("LAST_7_DAYS", 0) or 0
        last7_content = content.get("LAST_7_DAYS", 0) or 0

        last30_news = news.get("LAST_30_DAYS", 0) or 0
        last30_content = content.get("LAST_30_DAYS", 0) or 0

        top_companies.append({
            "id_company": company_id,
            "name": name,
            "is_partner": bool(news.get("IS_PARTNER")),

            # 🔹 SPLIT (pour ton front)
            "total_news": total_news,
            "total_analyses": total_content,

            # 🔹 AGRÉGÉ
            "total": total_news + total_content,
            "last_7_days": last7_news + last7_content,
            "last_30_days": last30_news + last30_content,
        })

    # --- tri final ---
    top_companies.sort(
        key=lambda x: x["total"],
        reverse=True
    )

    # =====================================================
    # RETURN
    # =====================================================

    return {
        "total_count": total_count,
        "last_7_days": last_7,
        "last_30_days": last_30,
        "topics_stats": topics_stats,
        "types_stats": types_stats,
        "top_companies": top_companies,
    }


# ============================================================
# LIST ALL COMPANIES — PUBLIC (FOR FILTER PANEL)
# ============================================================

def list_companies_public():
    sql = f"""
        SELECT
            c.ID_COMPANY,
            c.NAME,
            c.IS_PARTNER,
            COUNT(n.ID_NEWS) AS TOTAL_COUNT
        FROM `{TABLE_NEWS}` n
        JOIN `{TABLE_COMPANY}` c
          ON n.ID_COMPANY = c.ID_COMPANY
        WHERE
            n.STATUS = 'PUBLISHED'
            AND n.PUBLISHED_AT IS NOT NULL
        GROUP BY c.ID_COMPANY, c.NAME, c.IS_PARTNER
        ORDER BY TOTAL_COUNT DESC
    """

    rows = query_bq(sql)

    return [
        {
            "id_company": r["ID_COMPANY"],
            "name": r["NAME"],
            "is_partner": bool(r["IS_PARTNER"]),
            "total_count": r["TOTAL_COUNT"],
        }
        for r in rows
    ]



# ============================================================
# LIST BRÈVES — PUBLIC (PAGINÉ / PAR ANNÉE)
# ============================================================
def list_breves_public(
    year: int,
    limit: int = 20,
    cursor: Optional[str] = None,
):
    """
    Retourne les contenus publiés (BRÈVES + NEWS)
    rendus sous forme de brèves pour une année donnée,
    paginés par date (cursor-based).
    """

    params = {
        "year": year,
        "limit": limit,
    }

    cursor_clause = ""
    if cursor:
        cursor_clause = "AND n.PUBLISHED_AT < @cursor"
        params["cursor"] = cursor

    sql = f"""
        SELECT
            n.ID_NEWS,
            n.TITLE,
            n.EXCERPT,
            n.PUBLISHED_AT,

            -- SOCIÉTÉ
            c.NAME AS COMPANY_NAME,

            -- CATÉGORIE ÉDITORIALE
            n.NEWS_TYPE,

            -- TOPICS
            T.TOPICS

        FROM `{TABLE_NEWS}` n
        JOIN `{TABLE_COMPANY}` c
          ON n.ID_COMPANY = c.ID_COMPANY

        LEFT JOIN (
            SELECT
                NT.ID_NEWS,
                ARRAY_AGG(
                    STRUCT(
                        T.LABEL AS label,
                        T.TOPIC_AXIS AS axis
                    )
                ) AS TOPICS
            FROM `{TABLE_NEWS_TOPIC}` NT
            JOIN `{TABLE_TOPIC}` T
              ON NT.ID_TOPIC = T.ID_TOPIC
            GROUP BY NT.ID_NEWS
        ) T ON n.ID_NEWS = T.ID_NEWS

        WHERE
            n.STATUS = 'PUBLISHED'
            AND n.PUBLISHED_AT IS NOT NULL
            AND EXTRACT(YEAR FROM n.PUBLISHED_AT) = @year
            {cursor_clause}

        ORDER BY n.PUBLISHED_AT DESC
        LIMIT @limit
    """

    rows = query_bq(sql, params)

    return [
        {
            "id": r["ID_NEWS"],
            "title": r["TITLE"],
            "excerpt": r["EXCERPT"],
            "published_at": r["PUBLISHED_AT"],
            "company": r["COMPANY_NAME"],
            "news_type": r["NEWS_TYPE"],
            "topics": r.get("TOPICS") or [],
        }
        for r in rows
    ]


def list_news_admin(
    limit: int = 50,
    offset: int = 0,
    news_type: str | None = None,
    news_kind: str | None = None,
    company: str | None = None,
):
    where_clauses = []
    params = {
        "limit": limit,
        "offset": offset,
    }

    # ---------------------------
    # FILTRES
    # ---------------------------

    if news_type:
        where_clauses.append("n.NEWS_TYPE = @news_type")
        params["news_type"] = news_type

    if news_kind:
        where_clauses.append("n.NEWS_KIND = @news_kind")
        params["news_kind"] = news_kind

    if company:
        where_clauses.append("LOWER(c.NAME) LIKE LOWER(@company)")
        params["company"] = f"%{company}%"

    where_sql = ""
    if where_clauses:
        where_sql = "WHERE " + " AND ".join(where_clauses)

    # ---------------------------
    # QUERY
    # ---------------------------

    sql = f"""
        SELECT
            n.ID_NEWS,
            n.TITLE,
            n.STATUS,
            n.PUBLISHED_AT,
            n.CREATED_AT,
            n.NEWS_KIND,
            n.NEWS_TYPE,
            c.NAME AS COMPANY_NAME

        FROM `{TABLE_NEWS}` n
        JOIN `{TABLE_COMPANY}` c
          ON n.ID_COMPANY = c.ID_COMPANY

        {where_sql}

        ORDER BY
            
            IFNULL(n.PUBLISHED_AT, TIMESTAMP("1970-01-01")) DESC,

            CASE n.STATUS
                WHEN 'DRAFT' THEN 1
                WHEN 'SCHEDULED' THEN 2
                WHEN 'PUBLISHED' THEN 3
                ELSE 4
            END,

            n.CREATED_AT DESC

        LIMIT @limit
        OFFSET @offset
    """

    rows = query_bq(sql, params)

    # ---------------------------
    # MAPPING API (snake_case)
    # ---------------------------

    return [
        {
            "id_news": r["ID_NEWS"],
            "title": r["TITLE"],
            "status": r["STATUS"],
            "published_at": (
                r["PUBLISHED_AT"].isoformat()
                if r.get("PUBLISHED_AT")
                else None
            ),
            "news_kind": r["NEWS_KIND"],
            "news_type": r.get("NEWS_TYPE"),
            "company_name": r.get("COMPANY_NAME"),
        }
        for r in rows
    ]


def get_news_admin_stats():

    sql = f"""
        SELECT
            COUNT(*) AS TOTAL,

            COUNTIF(STATUS = 'PUBLISHED') AS TOTAL_PUBLISHED,
            COUNTIF(STATUS = 'DRAFT') AS TOTAL_DRAFT,

            COUNTIF(NEWS_KIND = 'NEWS') AS TOTAL_NEWS,
            COUNTIF(NEWS_KIND = 'BRIEF') AS TOTAL_BRIEVES,

            COUNTIF(
                STATUS = 'PUBLISHED'
                AND EXTRACT(YEAR FROM PUBLISHED_AT)
                    = EXTRACT(YEAR FROM CURRENT_TIMESTAMP())
            ) AS TOTAL_PUBLISHED_THIS_YEAR

        FROM `{TABLE_NEWS}`
    """

    rows = query_bq(sql)

    if not rows:
        return {
            "total": 0,
            "total_published": 0,
            "total_draft": 0,
            "total_news": 0,
            "total_briefs": 0,
            "total_published_this_year": 0,
        }

    r = rows[0]

    return {
        "total": r.get("TOTAL", 0) or 0,
        "total_published": r.get("TOTAL_PUBLISHED", 0) or 0,
        "total_draft": r.get("TOTAL_DRAFT", 0) or 0,
        "total_news": r.get("TOTAL_NEWS", 0) or 0,
        "total_briefs": r.get("TOTAL_BRIEVES", 0) or 0,
        "total_published_this_year": r.get("TOTAL_PUBLISHED_THIS_YEAR", 0) or 0,
    }




# ============================================================
# LINKEDIN
# ============================================================
def get_news_linkedin_post(news_id: str) -> Optional[dict]:
    client = get_bigquery_client()
    rows = list(
        client.query(
            f"""
            SELECT ID_NEWS, TEXT, MODE, UPDATED_AT
            FROM `{TABLE_NEWS_LINKEDIN_POST}`
            WHERE ID_NEWS = @id
            LIMIT 1
            """,
            job_config=bigquery.QueryJobConfig(
                query_parameters=[
                    bigquery.ScalarQueryParameter("id", "STRING", news_id)
                ]
            ),
        ).result()
    )
    if not rows:
        return None
    return serialize_row(dict(rows[0]))


def save_news_linkedin_post(news_id: str, text: str, mode: str):
    client = get_bigquery_client()
    now = datetime.utcnow()

    client.query(
        f"""
        MERGE `{TABLE_NEWS_LINKEDIN_POST}` T
        USING (
            SELECT
                @id_news AS ID_NEWS,
                @text AS TEXT,
                @mode AS MODE,
                @updated_at AS UPDATED_AT
        ) S
        ON T.ID_NEWS = S.ID_NEWS
        WHEN MATCHED THEN
          UPDATE SET
            TEXT = S.TEXT,
            MODE = S.MODE,
            UPDATED_AT = S.UPDATED_AT
        WHEN NOT MATCHED THEN
          INSERT (ID_NEWS, TEXT, MODE, UPDATED_AT)
          VALUES (S.ID_NEWS, S.TEXT, S.MODE, S.UPDATED_AT)
        """,
        job_config=bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("id_news", "STRING", news_id),
                bigquery.ScalarQueryParameter("text", "STRING", text),
                bigquery.ScalarQueryParameter("mode", "STRING", mode),
                bigquery.ScalarQueryParameter("updated_at", "TIMESTAMP", now),
            ]
        ),
    ).result()
