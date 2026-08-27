import uuid
from datetime import datetime, timezone, date
from typing import Optional, Dict, Any, List

from google.cloud import bigquery

from config import BQ_PROJECT, BQ_DATASET
from api.content.models import ContentCreate, ContentUpdate
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
TABLE_CONTENT_ENRICHED = (
    f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_CONTENT_ENRICHED"
)



# ============================================================
# UTILS
# ============================================================

def normalize_array(
    value,
):

    if value is None:
        return []

    if isinstance(
        value,
        list,
    ):

        return [

            str(v).strip()

            for v in value

            if str(v).strip()

        ]

    return []


# ============================================================
# CREATE CONTENT
# ============================================================

def create_content(
    data: ContentCreate,
) -> str:

    # ========================================================
    # VALIDATION
    # ========================================================

    if (
        not data.title
        or not data.title.strip()
    ):

        raise ValueError(
            "TITLE obligatoire"
        )

    if (
        not data.content_body
        or not data.content_body.strip()
    ):

        raise ValueError(
            "CONTENT_BODY obligatoire"
        )


    # ========================================================
    # META
    # ========================================================

    content_id = str(
        uuid.uuid4()
    )

    now = (
        datetime.now(
            timezone.utc
        )
        .isoformat()
    )


    # ========================================================
    # ROW
    # ========================================================

    row = [{

        "ID_CONTENT":
            content_id,

        "ID_PRIMARY_COMPANY":
            data.id_primary_company,

        "ID_RAW":
            data.id_raw,

        "STATUS":
            "DRAFT",

        "IS_ACTIVE":
            True,

        # ====================================================
        # SOURCE
        # ====================================================

        "SOURCE_ID":
            data.source_id,

        "SOURCE_URL":
            data.source_url,

        "SOURCE_TITLE":
            data.source_title,

        "SOURCE_PUBLISHED_AT": (
            data.source_published_at.isoformat()
            if data.source_published_at
            else None
        ),

        "SOURCE_DATE": (
            data.source_date.isoformat()
            if data.source_date
            else None
        ),

        # ====================================================
        # CONTENT
        # ====================================================

        "TITLE":
            data.title.strip(),

        "EXCERPT":
            data.excerpt,

        "CONTENT_BODY":
            data.content_body,

        # ====================================================
        # EXTRACTIONS
        # ====================================================

        "CHIFFRES":
            normalize_array(
                data.chiffres
            ),

        "ACTEURS_CITES":
            normalize_array(
                data.acteurs_cites
            ),

        "CONCEPTS_LLM":
            normalize_array(
                data.concepts_llm
            ),

        "SOLUTIONS_LLM":
            normalize_array(
                data.solutions_llm
            ),

        "TOPICS_LLM":
            normalize_array(
                data.topics_llm
            ),

        # ====================================================
        # ANALYSE
        # ====================================================

        "MECANIQUE_EXPLIQUEE":
            data.mecanique_expliquee,

        "ENJEU_STRATEGIQUE":
            data.enjeu_strategique,

        "POINT_DE_FRICTION":
            data.point_de_friction,

        "SIGNAL_ANALYTIQUE":
            data.signal_analytique,

        # ====================================================
        # PUBLICATION
        # ====================================================

        "PUBLISHED_AT":
            None,

        "CREATED_AT":
            now,

        "UPDATED_AT":
            now,

    }]


    # ========================================================
    # INSERT CONTENT
    # ========================================================

    client = (
        get_bigquery_client()
    )

    client.load_table_from_json(

        row,

        TABLE_CONTENT,

        job_config=(
            bigquery.LoadJobConfig(
                write_disposition="WRITE_APPEND"
            )
        ),

    ).result()

    print(
        "✔ INSERT DONE FOR:",
        content_id,
    )


    # ========================================================
    # PRIMARY COMPANY RELATION
    # ========================================================

    if data.id_primary_company:

        insert_bq(

            TABLE_CONTENT_COMPANY,

            [{

                "ID_CONTENT":
                    content_id,

                "ID_COMPANY":
                    data.id_primary_company,

                "CREATED_AT":
                    now,

            }],

        )


    # ========================================================
    # NUMBERS → BACKLOG PIPELINE
    # ========================================================

    try:

        chiffres = normalize_array(
            data.chiffres
        )

        if chiffres:

            backlog_rows = (
                get_numbers_from_content(
                    content_id
                )
            )

            processed_results = []

            for backlog_row in backlog_rows:

                result = (
                    process_backlog_row(
                        backlog_row
                    )
                )

                if (
                    result.get("status")
                    == "ok"
                ):

                    processed_results.append(
                        result
                    )

            if processed_results:

                insert_backlog_batch(
                    processed_results
                )

                print(
                    "✔ NUMBERS BACKLOG INSERTED:",
                    len(
                        processed_results
                    ),
                )

            else:

                print(
                    "ℹ️ NO VALID NUMBERS:",
                    content_id,
                )

        else:

            print(
                "ℹ️ NO CHIFFRES TO PROCESS:",
                content_id,
            )

    except Exception as e:

        print(
            "❌ ERROR NUMBERS BACKLOG:",
            str(e),
        )


    # ========================================================
    # DONE
    # ========================================================

    print(
        "✔ CONTENT CREATED:",
        content_id,
    )

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

def update_content(
    id_content: str,
    data: ContentUpdate,
):

    now = datetime.now(
        timezone.utc
    )

    fields = {}


    # ========================================================
    # PRIMARY COMPANY
    # ========================================================

    if data.id_primary_company is not None:

        fields[
            "ID_PRIMARY_COMPANY"
        ] = data.id_primary_company


    # ========================================================
    # SOURCE
    # ========================================================

    if data.source_id is not None:

        fields[
            "SOURCE_ID"
        ] = data.source_id


    if data.source_text is not None:

        fields[
            "SOURCE_TEXT"
        ] = data.source_text


    if data.source_url is not None:

        fields[
            "SOURCE_URL"
        ] = data.source_url


    if data.source_author is not None:

        fields[
            "SOURCE_AUTHOR"
        ] = data.source_author


    if data.source_published_at is not None:

        fields[
            "SOURCE_PUBLISHED_AT"
        ] = data.source_published_at


    if data.source_date is not None:

        fields[
            "SOURCE_DATE"
        ] = data.source_date


    # ========================================================
    # SUMMARY
    # ========================================================

    if data.title is not None:

        fields[
            "TITLE"
        ] = data.title.strip()


    if data.title_en is not None:

        fields[
            "TITLE_EN"
        ] = data.title_en.strip()


    if data.excerpt is not None:

        fields[
            "EXCERPT"
        ] = data.excerpt


    if data.excerpt_en is not None:

        fields[
            "EXCERPT_EN"
        ] = data.excerpt_en


    if data.content_body is not None:

        fields[
            "CONTENT_BODY"
        ] = data.content_body


    # ========================================================
    # EXTRACTIONS STRUCTURÉES
    # ========================================================

    if data.chiffres is not None:

        fields[
            "CHIFFRES"
        ] = normalize_array(
            data.chiffres
        )


    if data.acteurs_cites is not None:

        fields[
            "ACTEURS_CITES"
        ] = normalize_array(
            data.acteurs_cites
        )


    if data.concepts_llm is not None:

        fields[
            "CONCEPTS_LLM"
        ] = normalize_array(
            data.concepts_llm
        )


    if data.solutions_llm is not None:

        fields[
            "SOLUTIONS_LLM"
        ] = normalize_array(
            data.solutions_llm
        )


    if data.topics_llm is not None:

        fields[
            "TOPICS_LLM"
        ] = normalize_array(
            data.topics_llm
        )


    # ========================================================
    # ANALYSE STRATÉGIQUE
    # ========================================================

    if data.mecanique_expliquee is not None:

        fields[
            "MECANIQUE_EXPLIQUEE"
        ] = data.mecanique_expliquee


    if data.enjeu_strategique is not None:

        fields[
            "ENJEU_STRATEGIQUE"
        ] = data.enjeu_strategique


    if data.point_de_friction is not None:

        fields[
            "POINT_DE_FRICTION"
        ] = data.point_de_friction


    if data.signal_analytique is not None:

        fields[
            "SIGNAL_ANALYTIQUE"
        ] = data.signal_analytique


    # ========================================================
    # META
    # ========================================================

    fields[
        "UPDATED_AT"
    ] = now


    # ========================================================
    # UPDATE CONTENT
    # ========================================================

    update_bq(

        table=TABLE_CONTENT,

        fields=fields,

        where={
            "ID_CONTENT":
                id_content,
        },

    )


    # ========================================================
    # PRIMARY COMPANY RELATION
    # ========================================================

    if data.id_primary_company is not None:

        reset_and_insert(

            TABLE_CONTENT_COMPANY,

            "ID_COMPANY",

            id_content,

            (
                [
                    data.id_primary_company
                ]

                if data.id_primary_company

                else []
            ),

        )


    return True
# ============================================================
# GET CONTENT
# ============================================================

def get_content(
    content_id: str,
) -> dict | None:

    sql = f"""
    SELECT

        ID_CONTENT,

        SOURCE_ID,
        SOURCE_TITLE,
        SOURCE_URL,

        TITLE,
        TITLE_EN,

        EXCERPT,
        EXCERPT_EN,

        CONTENT_BODY,
        CONTENT_BODY_EN,

        SIGNAL_ANALYTIQUE,
        SIGNAL_ANALYTIQUE_EN,

        MECANIQUE_EXPLIQUEE,
        MECANIQUE_EXPLIQUEE_EN,

        ENJEU_STRATEGIQUE,
        ENJEU_STRATEGIQUE_EN,

        POINT_DE_FRICTION,
        POINT_DE_FRICTION_EN,

        CHIFFRES,

        ACTEURS_CITES,

        ID_PRIMARY_COMPANY,

        COMPANIES,

        SOLUTIONS,

        TOPICS,

        UNIVERSES,

        CONCEPTS,

        PUBLISHED_AT

    FROM `{TABLE_CONTENT_ENRICHED}`

    WHERE

        ID_CONTENT = @content_id

        AND IS_ACTIVE = TRUE

        AND STATUS = "PUBLISHED"

    LIMIT 1
    """

    rows = query_bq(

        sql,

        {
            "content_id":
                content_id,
        },

    )

    if not rows:
        return None

    return rows[0]
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
