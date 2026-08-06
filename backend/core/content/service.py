import uuid
from datetime import datetime, timezone, date
from typing import Optional, Dict, Any, List

from google.cloud import bigquery

from config import BQ_PROJECT, BQ_DATASET
from api.content.models import ContentCreate, ContentUpdate
from core.content.news_ai import generate_news
from utils.bigquery_utils import (
    query_bq,
    insert_bq,
    update_bq,
    get_bigquery_client,
)

from core.numbers.service import get_numbers_from_content
from core.numbers.backlog_llm import process_backlog_row
from core.numbers.backlog_insert_service import insert_backlog_batch

# ============================================================
# TABLES
# ============================================================

TABLE_CONTENT = f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_CONTENT"

TABLE_CONTENT_TOPIC = f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_CONTENT_TOPIC"
TABLE_CONTENT_COMPANY = f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_CONTENT_COMPANY"

TABLE_CONTENT_CONCEPT = f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_CONTENT_CONCEPT"
TABLE_CONTENT_SOLUTION = f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_CONTENT_SOLUTION"
TABLE_CONTENT_RAW = f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_CONTENT_RAW"

TABLE_TOPIC = f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_TOPIC"
TABLE_COMPANY = f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_COMPANY"
TABLE_CONCEPT = f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_CONCEPT"
TABLE_SOLUTION = f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_SOLUTION"
TABLE_SOURCE = f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_SOURCE"



# ============================================================
# UTILS
# ============================================================

def _normalize_array(value):
    if value is None:
        return []

    if isinstance(value, list):
        return [
            str(v).strip()
            for v in value
            if str(v).strip()
        ]

    return []

# ============================================================
# CREATE CONTENT
# ============================================================

def create_content(data: ContentCreate) -> str:

    if not data.title or not data.title.strip():
        raise ValueError("TITLE obligatoire")

    if not data.content_body or not data.content_body.strip():
        raise ValueError("CONTENT_BODY obligatoire")

    content_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()

    row = [{
        "ID_CONTENT": content_id,
        "ID_PRIMARY_COMPANY": data.id_primary_company,
        "STATUS": "DRAFT",
        "IS_ACTIVE": True,
        "AUTHOR": data.author,
        "SOURCE_ID": data.source_id,
        "SOURCE_PUBLISHED_AT": (
            data.source_published_at.isoformat()
            if data.source_published_at else None
        ),
        "TITLE": data.title.strip(),
        "EXCERPT": data.excerpt,
        "CONTENT_BODY": data.content_body,
        "CHIFFRES": normalize_array(data.chiffres),
        "ACTEURS_CITES": normalize_array(data.acteurs_cites),
        "CONCEPTS_LLM": normalize_array(data.concepts_llm),
        "SOLUTIONS_LLM": normalize_array(data.solutions_llm),
        "TOPICS_LLM": normalize_array(data.topics_llm),
        "MECANIQUE_EXPLIQUEE": data.mecanique_expliquee,
        "ENJEU_STRATEGIQUE": data.enjeu_strategique,
        "POINT_DE_FRICTION": data.point_de_friction,
        "SIGNAL_ANALYTIQUE": data.signal_analytique,
        "SEO_TITLE": data.seo_title,
        "SEO_DESCRIPTION": data.seo_description,
        "PUBLISHED_AT": None,
        "CREATED_AT": now,
        "SOURCE_DATE": (
            data.source_date.isoformat()
            if data.source_date else None
        ),
        "ID_RAW": data.id_raw,
        "SOURCE_URL": data.source_url,
        "SOURCE_TITLE": data.source_title,
        "UPDATED_AT": now,
    }]

    # ============================================================
    # INSERT CONTENT
    # ============================================================

    client = get_bigquery_client()

    client.load_table_from_json(
        row,
        TABLE_CONTENT,
        job_config=bigquery.LoadJobConfig(
            write_disposition="WRITE_APPEND"
        ),
    ).result()

    print("✔ INSERT DONE FOR:", content_id)

    # ============================================================
    # NUMBERS → BACKLOG PIPELINE
    # ============================================================

    try:

        chiffres = normalize_array(data.chiffres)

        if chiffres:

            backlog_rows = get_numbers_from_content(content_id)

            processed_results = []

            for backlog_row in backlog_rows:

                result = process_backlog_row(backlog_row)

                if result.get("status") == "ok":
                    processed_results.append(result)

            if processed_results:

                insert_backlog_batch(processed_results)

                print(
                    "✔ NUMBERS BACKLOG INSERTED:",
                    len(processed_results)
                )

            else:

                print("ℹ️ NO VALID NUMBERS:", content_id)

        else:

            print("ℹ️ NO CHIFFRES TO PROCESS:", content_id)

    except Exception as e:

        print("❌ ERROR NUMBERS BACKLOG:", str(e))

    # ============================================================
    # RELATIONS
    # ============================================================

    final_topics = (
        data.topics
        if data.topics
        else data.topics_llm
    )

    if final_topics:

        insert_bq(
            TABLE_CONTENT_TOPIC,
            [
                {
                    "ID_CONTENT": content_id,
                    "ID_TOPIC": tid,
                    "CREATED_AT": now,
                }
                for tid in set(final_topics)
                if tid
            ],
        )

    # ============================================================
    # COMPANIES
    # ============================================================

    final_companies = set(data.companies or [])

    if data.id_primary_company:
        final_companies.add(data.id_primary_company)

    if final_companies:

        insert_bq(
            TABLE_CONTENT_COMPANY,
            [
                {
                    "ID_CONTENT": content_id,
                    "ID_COMPANY": cid,
                    "CREATED_AT": now,
                }
                for cid in final_companies
            ],
        )

    # ============================================================
    # CONCEPTS
    # ============================================================

    final_concepts = (
        data.concepts
        if data.concepts
        else data.concepts_llm
    )

    if final_concepts:

        insert_bq(
            TABLE_CONTENT_CONCEPT,
            [
                {
                    "ID_CONTENT": content_id,
                    "ID_CONCEPT": cid,
                    "CREATED_AT": now,
                }
                for cid in set(final_concepts)
                if cid
            ],
        )

    # ============================================================
    # SOLUTIONS
    # ============================================================

    if data.solutions:

        insert_bq(
            TABLE_CONTENT_SOLUTION,
            [
                {
                    "ID_CONTENT": content_id,
                    "ID_SOLUTION": sid,
                    "CREATED_AT": now,
                }
                for sid in data.solutions
            ],
        )

    print("✔ RELATIONS DONE FOR:", content_id)

    return content_id

# ============================================================
# RESET RELATIONS
# ============================================================

def _reset_relations(table, id_field, id_content, values):

    client = get_bigquery_client()
    now = datetime.now(timezone.utc).isoformat()

    client.query(
        f"DELETE FROM `{table}` WHERE ID_CONTENT = @id",
        job_config=bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter(
                    "id", "STRING", id_content
                )
            ]
        ),
    ).result()

    if values:

        insert_bq(
            table,
            [
                {
                    "ID_CONTENT": id_content,
                    id_field: v,
                    "CREATED_AT": now,
                }
                for v in values
            ],
        )


# ============================================================
# UPDATE CONTENT
# ============================================================
def update_content(id_content: str, data: ContentUpdate):

    now = datetime.now(timezone.utc)

    fields = {}

    # ============================================================
    # 🔥 PRIMARY COMPANY
    # ============================================================

    if data.id_primary_company is not None:
        fields["ID_PRIMARY_COMPANY"] = data.id_primary_company

    # ============================================================
    # SOURCE
    # ============================================================

    if data.source_id is not None:
        fields["SOURCE_ID"] = data.source_id

    if data.source_url is not None:
        fields["SOURCE_URL"] = data.source_url

    if data.source_author is not None:
        fields["SOURCE_AUTHOR"] = data.source_author

    if data.source_published_at is not None:
        fields["SOURCE_PUBLISHED_AT"] = data.source_published_at

    # ============================================================
    # SUMMARY
    # ============================================================

    if data.title is not None:
        fields["TITLE"] = data.title.strip()

    if data.title_en is not None:
        fields["TITLE_EN"] = data.title_en.strip()

    if data.excerpt is not None:
        fields["EXCERPT"] = data.excerpt

    if data.excerpt_en is not None:
        fields["EXCERPT_EN"] = data.excerpt_en

    if data.content_body is not None:
        fields["CONTENT_BODY"] = data.content_body

    # ============================================================
    # EXTRACTIONS STRUCTURÉES
    # ============================================================

    if data.chiffres is not None:
        fields["CHIFFRES"] = normalize_array(data.chiffres)

    if data.acteurs_cites is not None:
        fields["ACTEURS_CITES"] = normalize_array(data.acteurs_cites)

    if data.concepts_llm is not None:
        fields["CONCEPTS_LLM"] = normalize_array(data.concepts_llm)

    if data.solutions_llm is not None:
        fields["SOLUTIONS_LLM"] = normalize_array(data.solutions_llm)

    if data.topics_llm is not None:
        fields["TOPICS_LLM"] = normalize_array(data.topics_llm)

    # ============================================================
    # ANALYSE STRATÉGIQUE
    # ============================================================

    if data.mecanique_expliquee is not None:
        fields["MECANIQUE_EXPLIQUEE"] = data.mecanique_expliquee

    if data.enjeu_strategique is not None:
        fields["ENJEU_STRATEGIQUE"] = data.enjeu_strategique

    if data.point_de_friction is not None:
        fields["POINT_DE_FRICTION"] = data.point_de_friction

    if data.signal_analytique is not None:
        fields["SIGNAL_ANALYTIQUE"] = data.signal_analytique

    # ============================================================
    # SEO
    # ============================================================

    if data.seo_title is not None:
        fields["SEO_TITLE"] = data.seo_title

    if data.seo_description is not None:
        fields["SEO_DESCRIPTION"] = data.seo_description

    # ============================================================
    # META
    # ============================================================

    if data.author is not None:
        fields["AUTHOR"] = data.author

    # Toujours mettre à jour UPDATED_AT
    fields["UPDATED_AT"] = now

    # ============================================================
    # UPDATE TABLE PRINCIPALE
    # ============================================================

    if fields:

        update_bq(
            table=TABLE_CONTENT,
            fields=fields,
            where={"ID_CONTENT": id_content},
        )

    # ============================================================
    # RESET RELATIONS
    # ============================================================

    reset_and_insert(
        TABLE_CONTENT_TOPIC,
        "ID_TOPIC",
        id_content,
        data.topics if data.topics is not None else [],
    )

    # ============================================================
    # 🔥 COMPANIES
    # ============================================================

    final_companies = set(data.companies or [])

    if data.id_primary_company:
        final_companies.add(data.id_primary_company)

    reset_and_insert(
        TABLE_CONTENT_COMPANY,
        "ID_COMPANY",
        id_content,
        list(final_companies),
    )

    reset_and_insert(
        TABLE_CONTENT_CONCEPT,
        "ID_CONCEPT",
        id_content,
        data.concepts if data.concepts is not None else [],
    )

    reset_and_insert(
        TABLE_CONTENT_SOLUTION,
        "ID_SOLUTION",
        id_content,
        data.solutions if data.solutions is not None else [],
    )
    
    return True

# ============================================================
# ARCHIVE CONTENT
# ============================================================

def archive_content(id_content: str):

    update_bq(
        table=TABLE_CONTENT,
        fields={"STATUS": "ARCHIVED"},
        where={"ID_CONTENT": id_content},
    )

    return True


def delete_content(id_content: str):

    client = get_bigquery_client()

    tables = [
        TABLE_CONTENT_TOPIC,
        TABLE_CONTENT_COMPANY,
        TABLE_CONTENT_CONCEPT,
        TABLE_CONTENT_SOLUTION,
    ]

    for table in tables:
        client.query(
            f"""
            DELETE FROM `{table}`
            WHERE ID_CONTENT = @id
            """,
            job_config=bigquery.QueryJobConfig(
                query_parameters=[
                    bigquery.ScalarQueryParameter(
                        "id", "STRING", id_content
                    ),
                ]
            ),
        ).result()

    client.query(
        f"""
        DELETE FROM `{TABLE_CONTENT}`
        WHERE ID_CONTENT = @id
        """,
        job_config=bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter(
                    "id", "STRING", id_content
                ),
            ]
        ),
    ).result()
