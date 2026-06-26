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
# SERIALIZATION
# ============================================================
def serialize_row(row: dict) -> dict:
    clean = {}
    for k, v in row.items():
        if hasattr(v, "isoformat"):
            clean[k] = v.isoformat()
        else:
            clean[k] = v
    return clean


# ============================================================
# CREATE NEWS / BRÈVE
# ============================================================

def create_news(data: NewsCreate) -> str:

    if not data.id_company:
        raise ValueError("id_company obligatoire")

    if not data.title or not data.title.strip():
        raise ValueError("title obligatoire")

    if data.news_kind not in ("NEWS", "BRIEF"):
        raise ValueError("news_kind invalide (NEWS | BRIEF)")

    news_id = str(uuid.uuid4())
    now = datetime.utcnow().isoformat()

    client = get_bigquery_client()

    # ============================================================
    # 1️⃣ INSERT NEWS
    # ============================================================

    row = [{
        "ID_NEWS": news_id,
        "STATUS": "DRAFT",
        "IS_ACTIVE": True,
        "NEWS_KIND": data.news_kind,
        "NEWS_TYPE": data.news_type,
        "ID_COMPANY": data.id_company,
        "TITLE": data.title.strip(),
        "EXCERPT": data.excerpt,
        "BODY": data.body if data.news_kind == "NEWS" else None,
        "MEDIA_RECTANGLE_ID": None,
        "HAS_VISUAL": False,
        "SOURCE_URL": data.source_url,
        "AUTHOR": data.author,
        "PUBLISHED_AT": None,
        "CREATED_AT": now,
        "UPDATED_AT": now,
        "IS_VECTORIZED": False,  # 🔥 important
    }]

    client.load_table_from_json(
        row,
        TABLE_NEWS,
        job_config=bigquery.LoadJobConfig(write_disposition="WRITE_APPEND"),
    ).result()

    # ============================================================
    # 2️⃣ LOGO SOCIÉTÉ
    # ============================================================

    logo_rows = query_bq(
        f"""
        SELECT MEDIA_LOGO_RECTANGLE_ID
        FROM `{TABLE_COMPANY}`
        WHERE ID_COMPANY = @company_id
        LIMIT 1
        """,
        {"company_id": data.id_company},
    )

    if logo_rows:
        logo = logo_rows[0].get("MEDIA_LOGO_RECTANGLE_ID")
        if logo:
            duplicate_company_visual_for_news(news_id, logo)

    # ============================================================
    # 3️⃣ RELATIONS
    # ============================================================

    if data.topics:
        insert_bq(
            TABLE_NEWS_TOPIC,
            [{"ID_NEWS": news_id, "ID_TOPIC": tid} for tid in data.topics],
        )

    if data.persons:
        insert_bq(
            TABLE_NEWS_PERSON,
            [{"ID_NEWS": news_id, "ID_PERSON": pid} for pid in data.persons],
        )

    if data.concepts:
        insert_bq(
            TABLE_NEWS_CONCEPT,
            [{"ID_NEWS": news_id, "ID_CONCEPT": cid} for cid in data.concepts],
        )

    if data.solutions:
        insert_bq(
            TABLE_NEWS_SOLUTION,
            [{"ID_NEWS": news_id, "ID_SOLUTION": sid} for sid in data.solutions],
        )

    # ============================================================
    # DONE
    # ============================================================

    return news_id


# ============================================================
# DUPLICATE COMPANY VISUAL FOR NEWS
# ============================================================

def duplicate_company_visual_for_news(id_news: str, company_media_id: str) -> str:
    from google.cloud import storage
    from google.oauth2 import service_account
    import os
    import json

    if not company_media_id or not company_media_id.startswith("COMPANY_"):
        raise ValueError("MEDIA société invalide")

    credentials_path = os.environ.get("GOOGLE_CREDENTIALS_FILE")
    if not credentials_path:
        raise ValueError("GOOGLE_CREDENTIALS_FILE non défini")

    with open(credentials_path, "r") as f:
        info = json.load(f)

    credentials = service_account.Credentials.from_service_account_info(info)

    storage_client = storage.Client(
        credentials=credentials,
        project=info.get("project_id"),
    )

    bucket = storage_client.bucket("ratecard-media")

    source_blob = bucket.blob(f"companies/{company_media_id}")

    if not source_blob.exists():
        raise ValueError("Fichier société introuvable")

    new_filename = f"NEWS_{id_news}_rect.jpg"
    destination_blob = bucket.blob(f"news/{new_filename}")

    destination_blob.rewrite(source_blob)

    # Update BQ
    update_bq(
        TABLE_NEWS,
        fields={
            "MEDIA_RECTANGLE_ID": new_filename,
            "HAS_VISUAL": True,
        },
        where={"ID_NEWS": id_news},
    )

    return new_filename
# ============================================================
# GET ONE NEWS / BRÈVE
# ============================================================
def get_news(id_news: str):

    rows = query_bq(
        f"""
        SELECT
            n.ID_NEWS,
            n.STATUS,
            n.NEWS_KIND,
            n.NEWS_TYPE,
            n.TITLE,
            n.EXCERPT,
            n.BODY,
            n.MEDIA_RECTANGLE_ID,
            n.HAS_VISUAL,
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

    news = {
        "id_news": r["ID_NEWS"],
        "status": r.get("STATUS"),
        "news_kind": r.get("NEWS_KIND"),
        "news_type": r.get("NEWS_TYPE"),

        "title": r.get("TITLE"),
        "excerpt": r.get("EXCERPT"),
        "body": r.get("BODY"),

        "media_rectangle_id": r.get("MEDIA_RECTANGLE_ID"),
        "has_visual": bool(r.get("HAS_VISUAL")),

        "source_url": r.get("SOURCE_URL"),
        "author": r.get("AUTHOR"),

        "published_at": (
            r["PUBLISHED_AT"].isoformat()
            if r.get("PUBLISHED_AT")
            else None
        ),
        "created_at": (
            r["CREATED_AT"].isoformat()
            if r.get("CREATED_AT")
            else None
        ),
        "updated_at": (
            r["UPDATED_AT"].isoformat()
            if r.get("UPDATED_AT")
            else None
        ),

        "company": {
            "id_company": r.get("ID_COMPANY"),
            "name": r.get("COMPANY_NAME"),
            "is_partner": bool(r.get("IS_PARTNER")),
        },
    }

    # ------------------------------------------------------------
    # TOPICS
    # ------------------------------------------------------------

    topic_rows = query_bq(
        f"""
        SELECT T.ID_TOPIC, T.LABEL
        FROM `{TABLE_NEWS_TOPIC}` NT
        JOIN `{TABLE_TOPIC}` T
          ON NT.ID_TOPIC = T.ID_TOPIC
        WHERE NT.ID_NEWS = @id
        """,
        {"id": id_news},
    )

    news["topics"] = [
        {
            "id_topic": t["ID_TOPIC"],
            "label": t["LABEL"],
        }
        for t in topic_rows
    ]

    # ------------------------------------------------------------
    # PERSONS
    # ------------------------------------------------------------

    person_rows = query_bq(
        f"""
        SELECT P.ID_PERSON, P.NAME
        FROM `{TABLE_NEWS_PERSON}` NP
        JOIN `{TABLE_PERSON}` P
          ON NP.ID_PERSON = P.ID_PERSON
        WHERE NP.ID_NEWS = @id
        """,
        {"id": id_news},
    )

    news["persons"] = [
        {
            "id_person": p["ID_PERSON"],
            "name": p["NAME"],
        }
        for p in person_rows
    ]

    # ------------------------------------------------------------
    # CONCEPTS
    # ------------------------------------------------------------

    concept_rows = query_bq(
        f"""
        SELECT C.ID_CONCEPT, C.LABEL
        FROM `{TABLE_NEWS_CONCEPT}` NC
        JOIN `{TABLE_CONCEPT}` C
          ON NC.ID_CONCEPT = C.ID_CONCEPT
        WHERE NC.ID_NEWS = @id
        """,
        {"id": id_news},
    )

    news["concepts"] = [
        {
            "id_concept": c["ID_CONCEPT"],
            "label": r["LABEL"],
        }
        for c in concept_rows
    ]

    # ------------------------------------------------------------
    # SOLUTIONS
    # ------------------------------------------------------------

    solution_rows = query_bq(
        f"""
        SELECT S.ID_SOLUTION, S.NAME
        FROM `{TABLE_NEWS_SOLUTION}` NS
        JOIN `{TABLE_SOLUTION}` S
          ON NS.ID_SOLUTION = S.ID_SOLUTION
        WHERE NS.ID_NEWS = @id
        """,
        {"id": id_news},
    )

    news["solutions"] = [
        {
            "id_solution": s["ID_SOLUTION"],
            "name": s["NAME"],
        }
        for s in solution_rows
    ]

    return news


# ============================================================
# LIST NEWS / BRÈVES (PUBLIC)
# ============================================================
def list_news(news_kind: str | None = None):
    where_kind = ""
    if news_kind:
        where_kind = f"AND n.NEWS_KIND = '{news_kind}'"

    sql = f"""
        SELECT
            n.ID_NEWS,
            n.NEWS_KIND,
            n.NEWS_TYPE,
            n.TITLE,
            n.EXCERPT,
            n.BODY,
            n.STATUS,
            n.PUBLISHED_AT,
            n.MEDIA_RECTANGLE_ID AS VISUAL_RECT_ID,
            n.HAS_VISUAL,
            c.ID_COMPANY,
            c.NAME AS COMPANY_NAME,
            c.MEDIA_LOGO_RECTANGLE_ID,
            c.IS_PARTNER,
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
            AND n.PUBLISHED_AT <= CURRENT_TIMESTAMP()
            {where_kind}
        ORDER BY n.PUBLISHED_AT DESC
    """

    return query_bq(sql)
# ============================================================
# NEWS TYPES (RÉFÉRENTIEL ÉDITORIAL)
# ============================================================

def list_news_types():
    rows = query_bq(
        f"""
        SELECT CODE, LABEL
        FROM `{BQ_PROJECT}.{BQ_DATASET}.RATECARD_NEWS_TYPE`
        WHERE IS_ACTIVE = TRUE
        ORDER BY LABEL
        """
    )

    return [
        {
            "code": r["CODE"],
            "label": r["LABEL"],
        }
        for r in rows
    ]


# ============================================================
# UPDATE NEWS / BRÈVE
# ============================================================

def update_news(id_news: str, data: NewsUpdate):

    values = data.dict(exclude_unset=True)
    if not values:
        return True

    field_map = {
        "news_kind": "NEWS_KIND",
        "news_type": "NEWS_TYPE",
        "id_company": "ID_COMPANY",
        "title": "TITLE",
        "excerpt": "EXCERPT",
        "body": "BODY",
        "media_rectangle_id": "MEDIA_RECTANGLE_ID",
        "source_url": "SOURCE_URL",
        "author": "AUTHOR",
    }

    fields = {}

    for k, v in values.items():
        if k in field_map:
            fields[field_map[k]] = v

    if "media_rectangle_id" in values:
        fields["HAS_VISUAL"] = bool(values["media_rectangle_id"])

    fields["UPDATED_AT"] = datetime.utcnow().isoformat()

    if fields:
        update_bq(
            table=TABLE_NEWS,
            fields=fields,
            where={"ID_NEWS": id_news},
        )

    client = get_bigquery_client()

    # TOPICS
    if data.topics is not None:
        client.query(
            f"DELETE FROM `{TABLE_NEWS_TOPIC}` WHERE ID_NEWS = @id",
            job_config=bigquery.QueryJobConfig(
                query_parameters=[
                    bigquery.ScalarQueryParameter("id", "STRING", id_news)
                ]
            ),
        ).result()

        if data.topics:
            insert_bq(
                TABLE_NEWS_TOPIC,
                [{"ID_NEWS": id_news, "ID_TOPIC": tid} for tid in data.topics],
            )

    # PERSONS
    if data.persons is not None:
        client.query(
            f"DELETE FROM `{TABLE_NEWS_PERSON}` WHERE ID_NEWS = @id",
            job_config=bigquery.QueryJobConfig(
                query_parameters=[
                    bigquery.ScalarQueryParameter("id", "STRING", id_news)
                ]
            ),
        ).result()

        if data.persons:
            insert_bq(
                TABLE_NEWS_PERSON,
                [{"ID_NEWS": id_news, "ID_PERSON": pid} for pid in data.persons],
            )

    # CONCEPTS
    if data.concepts is not None:
        client.query(
            f"DELETE FROM `{TABLE_NEWS_CONCEPT}` WHERE ID_NEWS = @id",
            job_config=bigquery.QueryJobConfig(
                query_parameters=[
                    bigquery.ScalarQueryParameter("id", "STRING", id_news)
                ]
            ),
        ).result()

        if data.concepts:
            insert_bq(
                TABLE_NEWS_CONCEPT,
                [{"ID_NEWS": id_news, "ID_CONCEPT": cid} for cid in data.concepts],
            )

    # SOLUTIONS
    if data.solutions is not None:
        client.query(
            f"DELETE FROM `{TABLE_NEWS_SOLUTION}` WHERE ID_NEWS = @id",
            job_config=bigquery.QueryJobConfig(
                query_parameters=[
                    bigquery.ScalarQueryParameter("id", "STRING", id_news)
                ]
            ),
        ).result()

        if data.solutions:
            insert_bq(
                TABLE_NEWS_SOLUTION,
                [{"ID_NEWS": id_news, "ID_SOLUTION": sid} for sid in data.solutions],
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


def delete_news(news_id: str):
    client = get_bigquery_client()

    queries = [
        f"DELETE FROM `{TABLE_NEWS}` WHERE ID_NEWS = @id",
        f"DELETE FROM `{TABLE_NEWS_TOPIC}` WHERE ID_NEWS = @id",
        f"DELETE FROM `{TABLE_NEWS_PERSON}` WHERE ID_NEWS = @id",
        f"DELETE FROM `{TABLE_NEWS_CONCEPT}` WHERE ID_NEWS = @id",
        f"DELETE FROM `{TABLE_NEWS_SOLUTION}` WHERE ID_NEWS = @id",
        f"DELETE FROM `{TABLE_NEWS_LINKEDIN_POST}` WHERE ID_NEWS = @id",
    ]

    job_config = bigquery.QueryJobConfig(
        query_parameters=[bigquery.ScalarQueryParameter("id", "STRING", news_id)]
    )

    for q in queries:
        client.query(q, job_config=job_config).result()
# ============================================================
# PUBLISH
# ============================================================
def publish_news(id_news: str, published_at: Optional[str] = None):

    rows = query_bq(
        f"""
        SELECT
            n.ID_COMPANY,
            n.NEWS_KIND,
            n.EXCERPT,
            n.MEDIA_RECTANGLE_ID,
            c.MEDIA_LOGO_RECTANGLE_ID AS COMPANY_RECT
        FROM `{TABLE_NEWS}` n
        JOIN `{TABLE_COMPANY}` c
          ON n.ID_COMPANY = c.ID_COMPANY
        WHERE n.ID_NEWS = @id
        """,
        {"id": id_news},
    )

    if not rows:
        raise ValueError("News introuvable")

    row = rows[0]

    # ============================================================
    # VALIDATION MINIMALE
    # ============================================================

    if not row["EXCERPT"]:
        raise ValueError("Un excerpt est requis pour publier")

    media_id = row["MEDIA_RECTANGLE_ID"]
    company_rect = row["COMPANY_RECT"]

    # ============================================================
    # 🔥 NORMALISATION VISUEL (NEWS + BRÈVES)
    # ============================================================

    if not media_id:
        if not company_rect:
            raise ValueError("Un visuel est requis pour publier")
        media_id = company_rect

    if media_id.startswith("COMPANY_"):

        from google.cloud import storage
        from google.oauth2 import service_account
        import os
        import json

        credentials_path = os.environ.get("GOOGLE_CREDENTIALS_FILE")
        if not credentials_path:
            raise ValueError("GOOGLE_CREDENTIALS_FILE non défini")

        with open(credentials_path, "r") as f:
            info = json.load(f)

        credentials = service_account.Credentials.from_service_account_info(info)

        storage_client = storage.Client(
            credentials=credentials,
            project=info.get("project_id"),
        )

        bucket = storage_client.bucket("ratecard-media")

        source_blob = bucket.blob(f"companies/{media_id}")

        if not source_blob.exists():
            raise ValueError("Logo société introuvable dans GCS")

        new_filename = f"NEWS_{id_news}_rect.jpg"
        destination_blob = bucket.blob(f"news/{new_filename}")

        destination_blob.rewrite(source_blob)

        update_bq(
            table=TABLE_NEWS,
            fields={
                "MEDIA_RECTANGLE_ID": new_filename,
                "HAS_VISUAL": True,
            },
            where={"ID_NEWS": id_news},
        )

        media_id = new_filename

    # ============================================================
    # DATE & STATUS
    # ============================================================

    now = datetime.now(timezone.utc)

    if published_at:
        if isinstance(published_at, str):
            publish_date = datetime.fromisoformat(published_at)
        else:
            publish_date = published_at

        if publish_date.tzinfo is None:
            publish_date = publish_date.replace(tzinfo=timezone.utc)
    else:
        publish_date = now

    status = "PUBLISHED" if publish_date <= now else "SCHEDULED"

    update_bq(
        table=TABLE_NEWS,
        fields={
            "STATUS": status,
            "PUBLISHED_AT": publish_date.isoformat(),
            "UPDATED_AT": now.isoformat(),
        },
        where={"ID_NEWS": id_news},
    )

    # ============================================================
    # 🚀 AUTO VECTORISATION (ONLY IF PUBLISHED)
    # ============================================================

    if status == "PUBLISHED":
        try:
            from core.vectorization.vector_service import vectorize_news

            print("🚀 AUTO VECTORIZE NEWS (PUBLISH):", id_news)

            vectorize_news(id_news)

        except Exception as e:
            print("❌ VECTORISATION ERROR:", str(e))

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
