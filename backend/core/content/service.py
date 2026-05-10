import re
import uuid
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timezone, date
from typing import Optional, Dict, Any, List
from urllib.parse import urljoin

from google.cloud import bigquery

from config import BQ_PROJECT, BQ_DATASET
from api.content.models import ContentCreate, ContentUpdate
from core.content.ai import generate_summary
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
from core.content.publish_sync_service import (
    after_publish_sync,
)

# ============================================================
# TABLES
# ============================================================

TABLE_CONTENT = f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_CONTENT"

TABLE_CONTENT_TOPIC = f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_CONTENT_TOPIC"
TABLE_CONTENT_EVENT = f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_CONTENT_EVENT"
TABLE_CONTENT_COMPANY = f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_CONTENT_COMPANY"
TABLE_CONTENT_PERSON = f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_CONTENT_PERSON"

TABLE_CONTENT_CONCEPT = f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_CONTENT_CONCEPT"
TABLE_CONTENT_SOLUTION = f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_CONTENT_SOLUTION"
TABLE_CONTENT_RAW = f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_CONTENT_RAW"

TABLE_TOPIC = f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_TOPIC"
TABLE_EVENT = f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_EVENT"
TABLE_COMPANY = f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_COMPANY"
TABLE_PERSON = f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_PERSON"
TABLE_CONCEPT = f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_CONCEPT"
TABLE_SOLUTION = f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_SOLUTION"
TABLE_SOURCE = f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_SOURCE"



# ============================================================
# UTILS
# ============================================================

def normalize_array(value):
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

        # 🔥 NEW
        "CONTENT_TYPE": (
            data.content_type
            if data.content_type
            else "ANALYSIS"
        ),

        # 🔥 NEW
        "ID_PRIMARY_COMPANY": data.id_primary_company,

        "STATUS": "DRAFT",
        "IS_ACTIVE": True,
        "AUTHOR": data.author,

        "SOURCE_ID": data.source_id,

        "SOURCE_PUBLISHED_AT": (
            data.source_published_at.isoformat()
            if data.source_published_at
            else None
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
            if data.source_date
            else None
        ),

        "UPDATED_AT": now,
    }]

    # ============================================================
    # DEBUG AVANT INSERT
    # ============================================================

    print("\n========== DEBUG CREATE_CONTENT ==========")
    print("ID_CONTENT:", content_id)

    debug_row = row[0]

    for field in ["CONCEPTS_LLM", "SOLUTIONS_LLM", "TOPICS_LLM"]:

        value = debug_row.get(field)

        print(f"\nFIELD: {field}")
        print("TYPE:", type(value))
        print("VALUE:", value)

        if isinstance(value, list):

            for i, v in enumerate(value):
                print(f"  [{i}] -> ({type(v)}) {v}")

    print("\nFULL ROW TYPES:")

    for k, v in debug_row.items():
        print(k, "=>", type(v))

    print("==========================================\n")

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

        # 🔥 NEW
        content_type = (
            data.content_type
            if data.content_type
            else "ANALYSIS"
        )

        chiffres = normalize_array(data.chiffres)

        # 🔥 NEW
        # Les NEWS ne déclenchent pas le pipeline backlog
        if content_type == "NEWS":

            print(
                "ℹ️ NEWS CONTENT → SKIP NUMBERS BACKLOG:",
                content_id
            )

        elif chiffres:

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

    if data.events:

        insert_bq(
            TABLE_CONTENT_EVENT,
            [
                {
                    "ID_CONTENT": content_id,
                    "ID_EVENT": eid,
                    "CREATED_AT": now,
                }
                for eid in data.events
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

    if data.persons:

        insert_bq(
            TABLE_CONTENT_PERSON,
            [
                {
                    "ID_CONTENT": content_id,
                    "ID_PERSON": p.id_person,
                    "ROLE": p.role,
                    "CREATED_AT": now,
                }
                for p in data.persons
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
# GET CONTENT
# ============================================================

def get_content(id_content: str):

    rows = query_bq(
        f"""
        SELECT
          ID_CONTENT,

          -- 🔥 NEW
          CONTENT_TYPE,

          -- 🔥 NEW
          ID_PRIMARY_COMPANY,

          STATUS,
          SOURCE_ID,
          TITLE,
          EXCERPT,
          CONTENT_BODY,
          CHIFFRES,
          ACTEURS_CITES,
          CONCEPTS_LLM,
          SOLUTIONS_LLM,
          TOPICS_LLM,
          MECANIQUE_EXPLIQUEE,
          ENJEU_STRATEGIQUE,
          POINT_DE_FRICTION,
          SIGNAL_ANALYTIQUE,
          PUBLISHED_AT
        FROM `{TABLE_CONTENT}`
        WHERE ID_CONTENT = @id
        LIMIT 1
        """,
        {"id": id_content},
    )

    if not rows:
        return None

    row = rows[0]

    def map_dt(value):
        return value.isoformat() if value else None

    content = {
        "id_content": row["ID_CONTENT"],

        # 🔥 NEW
        "content_type": (
            row.get("CONTENT_TYPE")
            or "ANALYSIS"
        ),

        # 🔥 NEW
        "id_primary_company": row.get("ID_PRIMARY_COMPANY"),

        "status": row.get("STATUS"),
        "source_id": row.get("SOURCE_ID"),

        "title": row.get("TITLE"),
        "excerpt": row.get("EXCERPT"),
        "content_body": row.get("CONTENT_BODY"),

        "chiffres": row.get("CHIFFRES") or [],
        "acteurs_cites": row.get("ACTEURS_CITES") or [],

        "concepts_llm": row.get("CONCEPTS_LLM") or [],
        "solutions_llm": row.get("SOLUTIONS_LLM") or [],
        "topics_llm": row.get("TOPICS_LLM") or [],

        "mecanique_expliquee": row.get("MECANIQUE_EXPLIQUEE"),
        "enjeu_strategique": row.get("ENJEU_STRATEGIQUE"),
        "point_de_friction": row.get("POINT_DE_FRICTION"),
        "signal_analytique": row.get("SIGNAL_ANALYTIQUE"),

        "published_at": map_dt(row.get("PUBLISHED_AT")),
    }

    # ============================================================
    # RELATIONS — MAPPING SNAKE_CASE
    # ============================================================

    topic_rows = query_bq(
        f"""
        SELECT T.ID_TOPIC, T.LABEL, T.TOPIC_AXIS
        FROM `{TABLE_CONTENT_TOPIC}` CT
        JOIN `{TABLE_TOPIC}` T
          ON CT.ID_TOPIC = T.ID_TOPIC
        WHERE CT.ID_CONTENT = @id
        """,
        {"id": id_content},
    )

    content["topics"] = [
        {
            "id_topic": r["ID_TOPIC"],
            "label": r["LABEL"],
            "topic_axis": r.get("TOPIC_AXIS"),
        }
        for r in topic_rows
    ]

    event_rows = query_bq(
        f"""
        SELECT E.ID_EVENT, E.LABEL
        FROM `{TABLE_CONTENT_EVENT}` CE
        JOIN `{TABLE_EVENT}` E
          ON CE.ID_EVENT = E.ID_EVENT
        WHERE CE.ID_CONTENT = @id
        """,
        {"id": id_content},
    )

    content["events"] = [
        {
            "id_event": r["ID_EVENT"],
            "label": r["LABEL"],
        }
        for r in event_rows
    ]

    company_rows = query_bq(
        f"""
        SELECT C.ID_COMPANY, C.NAME
        FROM `{TABLE_CONTENT_COMPANY}` CC
        JOIN `{TABLE_COMPANY}` C
          ON CC.ID_COMPANY = C.ID_COMPANY
        WHERE CC.ID_CONTENT = @id
        """,
        {"id": id_content},
    )

    content["companies"] = [
        {
            "id_company": r["ID_COMPANY"],
            "name": r["NAME"],
        }
        for r in company_rows
    ]

    # ============================================================
    # PRIMARY COMPANY
    # ============================================================

    primary_company = next(
        (
            c for c in content["companies"]
            if c["id_company"] == content["id_primary_company"]
        ),
        None
    )

    content["primary_company"] = primary_company

    person_rows = query_bq(
        f"""
        SELECT P.ID_PERSON, P.NAME, CP.ROLE
        FROM `{TABLE_CONTENT_PERSON}` CP
        JOIN `{TABLE_PERSON}` P
          ON CP.ID_PERSON = P.ID_PERSON
        WHERE CP.ID_CONTENT = @id
        """,
        {"id": id_content},
    )

    content["persons"] = [
        {
            "id_person": r["ID_PERSON"],
            "name": r["NAME"],
            "role": r.get("ROLE"),
        }
        for r in person_rows
    ]

    concept_rows = query_bq(
        f"""
        SELECT C.ID_CONCEPT, C.LABEL
        FROM `{TABLE_CONTENT_CONCEPT}` CC
        JOIN `{TABLE_CONCEPT}` C
          ON CC.ID_CONCEPT = C.ID_CONCEPT
        WHERE CC.ID_CONTENT = @id
        """,
        {"id": id_content},
    )

    content["concepts"] = [
        {
            "id_concept": r["ID_CONCEPT"],
            "label": r["LABEL"],
        }
        for r in concept_rows
    ]

    solution_rows = query_bq(
        f"""
        SELECT S.ID_SOLUTION, S.NAME
        FROM `{TABLE_CONTENT_SOLUTION}` CS
        JOIN `{TABLE_SOLUTION}` S
          ON CS.ID_SOLUTION = S.ID_SOLUTION
        WHERE CS.ID_CONTENT = @id
        """,
        {"id": id_content},
    )

    content["solutions"] = [
        {
            "id_solution": r["ID_SOLUTION"],
            "name": r["NAME"],
        }
        for r in solution_rows
    ]

    return content

# ============================================================
# LIST CONTENTS (PUBLIC)
# ============================================================

def list_contents():

    rows = query_bq(
        f"""
        SELECT
          c.ID_CONTENT,

          c.CONTENT_TYPE,

          -- 🔥 NEW
          c.ID_PRIMARY_COMPANY,

          pc.NAME AS PRIMARY_COMPANY_NAME,

          c.TITLE,
          c.EXCERPT,

          c.PUBLISHED_AT

        FROM `{TABLE_CONTENT}` c

        -- 🔥 NEW
        LEFT JOIN `{TABLE_COMPANY}` pc
          ON c.ID_PRIMARY_COMPANY = pc.ID_COMPANY

        WHERE
          c.STATUS = 'PUBLISHED'
          AND c.IS_ACTIVE = TRUE

        ORDER BY c.PUBLISHED_AT DESC
        """
    )

    def map_dt(value):
        return value.isoformat() if value else None

    return [
        {
            "id_content": r["ID_CONTENT"],

            # 🔥 NEW
            "content_type": (
                r.get("CONTENT_TYPE")
                or "ANALYSIS"
            ),

            # 🔥 NEW
            "id_primary_company": r.get(
                "ID_PRIMARY_COMPANY"
            ),

            "primary_company_name": r.get(
                "PRIMARY_COMPANY_NAME"
            ),

            "title": r["TITLE"],

            "excerpt": r.get("EXCERPT"),

            "published_at": map_dt(
                r.get("PUBLISHED_AT")
            ),
        }
        for r in rows
    ]

def list_active_sources():

    rows = query_bq(f"""
        SELECT
            SOURCE_ID as id_source,
            NAME as label
        FROM `{TABLE_SOURCE}`
        ORDER BY NAME
    """)

    return rows

# ============================================================
# LIST CONTENTS ADMIN
# ============================================================

def list_contents_admin():

    rows = query_bq(
        f"""
        SELECT
          c.ID_CONTENT,

          c.CONTENT_TYPE,

          -- 🔥 NEW
          c.ID_PRIMARY_COMPANY,

          pc.NAME AS PRIMARY_COMPANY_NAME,

          c.TITLE,

          c.STATUS,

          c.SOURCE_DATE,

          c.PUBLISHED_AT,

          c.UPDATED_AT

        FROM `{TABLE_CONTENT}` c

        -- 🔥 NEW
        LEFT JOIN `{TABLE_COMPANY}` pc
          ON c.ID_PRIMARY_COMPANY = pc.ID_COMPANY

        WHERE c.IS_ACTIVE = TRUE

        ORDER BY c.UPDATED_AT DESC
        """
    )

    return [
        {
            "id_content": r["ID_CONTENT"],

            # 🔥 NEW
            "content_type": (
                r.get("CONTENT_TYPE")
                or "ANALYSIS"
            ),

            # 🔥 NEW
            "id_primary_company": r.get(
                "ID_PRIMARY_COMPANY"
            ),

            "primary_company_name": r.get(
                "PRIMARY_COMPANY_NAME"
            ),

            "title": r["TITLE"],

            "status": r["STATUS"],

            "source_date": (
                r["SOURCE_DATE"].isoformat()
                if r.get("SOURCE_DATE")
                else None
            ),

            "published_at": (
                r["PUBLISHED_AT"].isoformat()
                if r.get("PUBLISHED_AT")
                else None
            ),

            "updated_at": (
                r["UPDATED_AT"].isoformat()
                if r.get("UPDATED_AT")
                else None
            ),
        }
        for r in rows
    ]

# ============================================================
# STORE RAW CONTENT
# ============================================================

def store_raw_content(
    source_id: str,
    source_title: str,
    raw_text: str,
    date_source: Optional[date] = None,

    # 🔥 NEW
    content_type: str = "ANALYSIS",

    # 🔥 NEW
    id_primary_company: Optional[str] = None,
) -> str:

    if not source_id:
        raise ValueError("source_id obligatoire")

    if not source_title or not source_title.strip():
        raise ValueError("source_title obligatoire")

    if not raw_text or not raw_text.strip():
        raise ValueError("raw_text vide")

    raw_id = str(uuid.uuid4())

    now_iso = datetime.utcnow().isoformat()

    row = [{

        "ID_RAW": raw_id,

        # 🔥 NEW
        "CONTENT_TYPE": content_type,

        # 🔥 NEW
        "ID_PRIMARY_COMPANY": id_primary_company,

        "SOURCE_ID": source_id,

        "SOURCE_TITLE": source_title.strip(),

        "RAW_TEXT": raw_text.strip(),

        "DATE_SOURCE": (
            date_source.isoformat()
            if date_source
            else None
        ),

        "STATUS": "STORED",

        "CREATED_AT": now_iso,

        "PROCESSED_AT": None,

        "GENERATED_CONTENT_ID": None,

        "ERROR_MESSAGE": None,
    }]

    client = get_bigquery_client()

    client.load_table_from_json(
        row,
        TABLE_CONTENT_RAW,
        job_config=bigquery.LoadJobConfig(
            write_disposition="WRITE_APPEND"
        ),
    ).result()

    return raw_id

def normalize_llm_list(values):
    output = []

    for v in values or []:
        if not v:
            continue

        parts = re.split(r",|;", v)

        for p in parts:
            clean = p.strip()
            if clean:
                output.append(clean)

    return list(dict.fromkeys(output))

def list_raw_stock(
    status: Optional[str] = None,
    source_id: Optional[str] = None,
    import_type: Optional[str] = None,

    # 🔥 NEW
    content_type: Optional[str] = None,
    id_primary_company: Optional[str] = None,

    limit: int = 50,
    offset: int = 0,
):

    conditions = []
    params = {}

    if status:
        conditions.append("r.STATUS = @status")
        params["status"] = status

    if source_id:
        conditions.append("r.SOURCE_ID = @source_id")
        params["source_id"] = source_id

    if import_type:
        conditions.append("r.IMPORT_TYPE = @import_type")
        params["import_type"] = import_type

    # 🔥 NEW
    if content_type:
        conditions.append("r.CONTENT_TYPE = @content_type")
        params["content_type"] = content_type

    # 🔥 NEW
    if id_primary_company:
        conditions.append(
            "r.ID_PRIMARY_COMPANY = @id_primary_company"
        )
        params["id_primary_company"] = id_primary_company

    where_clause = ""

    if conditions:
        where_clause = "WHERE " + " AND ".join(conditions)

    query = f"""
        SELECT
            r.ID_RAW,
            r.CONTENT_TYPE,

            -- 🔥 NEW
            r.ID_PRIMARY_COMPANY,

            c.NAME AS PRIMARY_COMPANY_NAME,

            r.SOURCE_ID,
            s.NAME AS SOURCE_NAME,

            r.SOURCE_TITLE,
            r.DATE_SOURCE,

            r.STATUS,
            r.ERROR_MESSAGE,

            r.CREATED_AT,
            r.IMPORT_TYPE,

            COUNT(*) OVER() AS TOTAL_COUNT

        FROM `{TABLE_CONTENT_RAW}` r

        LEFT JOIN `{BQ_PROJECT}.{BQ_DATASET}.RATECARD_SOURCE` s
            ON r.SOURCE_ID = s.SOURCE_ID

        -- 🔥 NEW
        LEFT JOIN `{TABLE_COMPANY}` c
            ON r.ID_PRIMARY_COMPANY = c.ID_COMPANY

        {where_clause}

        ORDER BY r.CREATED_AT DESC

        LIMIT @limit
        OFFSET @offset
    """

    params["limit"] = limit
    params["offset"] = offset

    rows = query_bq(query, params)

    total = rows[0]["TOTAL_COUNT"] if rows else 0

    return {
        "rows": [
            {
                "id_raw": r["ID_RAW"],

                "content_type": (
                    r.get("CONTENT_TYPE")
                    or "ANALYSIS"
                ),

                # 🔥 NEW
                "id_primary_company": r.get(
                    "ID_PRIMARY_COMPANY"
                ),

                "primary_company_name": r.get(
                    "PRIMARY_COMPANY_NAME"
                ),

                "source_id": r["SOURCE_ID"],

                "source_name": r.get("SOURCE_NAME"),

                "source_title": r["SOURCE_TITLE"],

                "date_source": r.get("DATE_SOURCE"),

                "status": r["STATUS"],

                "error_message": r.get("ERROR_MESSAGE"),

                "created_at": r["CREATED_AT"],

                "import_type": r.get("IMPORT_TYPE"),
            }
            for r in rows
        ],

        "total": total,
    }
def destock_all_raw_contents(batch_size: int = 50):

    total_processed = 0
    total_errors = 0

    while True:

        result = destock_raw_contents(limit=batch_size)

        if result["total_selected"] == 0:
            break

        # 🔐 Sécurité anti-boucle infinie
        if result["processed"] == 0:
            print("Aucun traitement réussi dans ce batch → arrêt de sécurité")
            break

        total_processed += result["processed"]
        total_errors += result["errors"]

        print(
            f"Batch terminé → processed: {result['processed']} | errors: {result['errors']}"
        )

    return {
        "total_processed": total_processed,
        "total_errors": total_errors,
    }


# ============================================================
# DESTOCK RAW CONTENTS
# ============================================================

def destock_raw_contents(
    limit: int = 5,
    specific_id: Optional[str] = None
) -> Dict[str, Any]:

    # ====================================================
    # 1️⃣ SELECT RAW(S)
    # ====================================================

    if specific_id:

        raws = query_bq(
            f"""
            SELECT *
            FROM `{TABLE_CONTENT_RAW}`
            WHERE ID_RAW = @id_raw
            """,
            {"id_raw": specific_id}
        )

    else:

        raws = query_bq(
            f"""
            SELECT *
            FROM `{TABLE_CONTENT_RAW}`
            WHERE STATUS = 'STORED'
            ORDER BY CREATED_AT DESC
            LIMIT {limit}
            """
        )

    processed = 0
    errors = 0

    # ====================================================
    # 2️⃣ PROCESS LOOP
    # ====================================================

    for raw in raws:

        raw_id = raw["ID_RAW"]

        try:

            print("\n==============================")
            print("RAW ID:", raw_id)
            print("SOURCE_ID:", raw.get("SOURCE_ID"))

            # 🔥 NEW
            print("CONTENT_TYPE:", raw.get("CONTENT_TYPE"))

            # 🔥 NEW
            print(
                "ID_PRIMARY_COMPANY:",
                raw.get("ID_PRIMARY_COMPANY")
            )

            print("RAW LENGTH:", len(raw.get("RAW_TEXT", "") or ""))
            print("------------------------------")

            if raw["STATUS"] not in ["STORED", "ERROR"]:
                raise ValueError("RAW non traitable (status invalide)")

            # ====================================================
            # PASS TO PROCESSING
            # ====================================================

            update_bq(
                TABLE_CONTENT_RAW,
                {
                    "STATUS": "PROCESSING",
                    "ERROR_MESSAGE": None,
                },
                where={"ID_RAW": raw_id}
            )

            # ====================================================
            # CONTENT TYPE
            # ====================================================

            content_type = (
                raw.get("CONTENT_TYPE")
                or "ANALYSIS"
            )

            # 🔥 NEW
            id_primary_company = raw.get(
                "ID_PRIMARY_COMPANY"
            )

            # ====================================================
            # GENERATE CONTENT
            # ====================================================

            if content_type == "NEWS":

                summary = generate_news(
                    source_id=raw.get("SOURCE_ID"),
                    source_text=raw.get("RAW_TEXT", "")
                )

            else:

                summary = generate_summary(
                    source_id=raw.get("SOURCE_ID"),
                    source_text=raw.get("RAW_TEXT", "")
                )

            concepts_llm = normalize_llm_list(
                summary.get("concepts", [])
            )

            solutions_llm = normalize_llm_list(
                summary.get("solutions", [])
            )

            topics_llm = normalize_llm_list(
                summary.get("topics", [])
            )

            acteurs_clean = normalize_llm_list(
                summary.get("acteurs_cites", [])
            )

            # ====================================================
            # CLEAN SOURCE_DATE
            # ====================================================

            raw_source_date = raw.get("DATE_SOURCE")

            source_date_clean = None

            if raw_source_date:

                if (
                    isinstance(raw_source_date, date)
                    and not isinstance(raw_source_date, datetime)
                ):

                    source_date_clean = raw_source_date

                elif isinstance(raw_source_date, datetime):

                    source_date_clean = raw_source_date.date()

                elif isinstance(raw_source_date, str):

                    try:

                        source_date_clean = datetime.strptime(
                            raw_source_date.split("T")[0],
                            "%Y-%m-%d"
                        )

                    except Exception:

                        source_date_clean = None

            # ====================================================
            # BUILD CONTENT MODEL
            # ====================================================

            content_payload = ContentCreate(

                # 🔥 NEW
                content_type=content_type,

                # 🔥 NEW
                id_primary_company=id_primary_company,

                title=summary.get("title"),

                excerpt=summary.get("excerpt"),

                content_body=summary.get("content_body"),

                chiffres=summary.get("chiffres", []),

                acteurs_cites=summary.get("acteurs_cites", []),

                concepts_llm=concepts_llm,

                solutions_llm=solutions_llm,

                topics_llm=topics_llm,

                mecanique_expliquee=summary.get("mecanique_expliquee"),

                enjeu_strategique=summary.get("enjeu_strategique"),

                point_de_friction=summary.get("point_de_friction"),

                signal_analytique=summary.get("signal_analytique"),

                source_id=raw.get("SOURCE_ID"),

                source_date=source_date_clean,

                author=None,
            )

            content_id = create_content(content_payload)

            # ====================================================
            # MARK RAW AS PROCESSED
            # ====================================================

            update_bq(
                TABLE_CONTENT_RAW,
                {
                    "STATUS": "PROCESSED",
                    "PROCESSED_AT": datetime.utcnow(),
                    "GENERATED_CONTENT_ID": content_id,
                    "ERROR_MESSAGE": None,
                },
                where={"ID_RAW": raw_id}
            )

            processed += 1

        except Exception as e:

            print("\n❌ ERROR DURING DESTOCK:", str(e))

            update_bq(
                TABLE_CONTENT_RAW,
                {
                    "STATUS": "ERROR",
                    "ERROR_MESSAGE": str(e),
                },
                where={"ID_RAW": raw_id}
            )

            errors += 1

    return {
        "processed": processed,
        "errors": errors,
        "total_selected": len(raws),
    }

def delete_raw_content(id_raw: str) -> None:

    if not id_raw:
        raise ValueError("id_raw obligatoire")

    query = f"""
        DELETE FROM `{TABLE_CONTENT_RAW}`
        WHERE ID_RAW = @id_raw
    """

    query_bq(
        query,
        {"id_raw": id_raw}
    )

def retry_raw_content(id_raw: str) -> None:

    if not id_raw:
        raise ValueError("id_raw obligatoire")

    # Vérifier que le RAW est bien en ERROR
    check_query = f"""
        SELECT STATUS
        FROM `{TABLE_CONTENT_RAW}`
        WHERE ID_RAW = @id_raw
    """

    rows = query_bq(check_query, {"id_raw": id_raw})

    if not rows:
        raise ValueError("RAW introuvable")

    if rows[0]["STATUS"] != "ERROR":
        raise ValueError("Retry autorisé uniquement pour les ERROR")

    # Reset propre
    update_bq(
        TABLE_CONTENT_RAW,
        {
            "STATUS": "STORED",
            "ERROR_MESSAGE": None,
        },
        where={"ID_RAW": id_raw}
    )

def get_raw_detail(id_raw: str):

    if not id_raw:
        raise ValueError("id_raw obligatoire")

    query = f"""
        SELECT
            r.ID_RAW,

            r.CONTENT_TYPE,

            -- 🔥 NEW
            r.ID_PRIMARY_COMPANY,

            c.NAME AS PRIMARY_COMPANY_NAME,

            r.SOURCE_ID,
            r.SOURCE_TITLE,

            r.DATE_SOURCE,

            r.RAW_TEXT,

            r.STATUS,
            r.ERROR_MESSAGE,

            r.IMPORT_TYPE,

            r.CREATED_AT

        FROM `{TABLE_CONTENT_RAW}` r

        -- 🔥 NEW
        LEFT JOIN `{TABLE_COMPANY}` c
            ON r.ID_PRIMARY_COMPANY = c.ID_COMPANY

        WHERE r.ID_RAW = @id_raw

        LIMIT 1
    """

    rows = query_bq(query, {"id_raw": id_raw})

    if not rows:
        return None

    r = rows[0]

    return {

        "id_raw": r["ID_RAW"],

        "content_type": (
            r.get("CONTENT_TYPE")
            or "ANALYSIS"
        ),

        # 🔥 NEW
        "id_primary_company": r.get(
            "ID_PRIMARY_COMPANY"
        ),

        "primary_company_name": r.get(
            "PRIMARY_COMPANY_NAME"
        ),

        "source_id": r["SOURCE_ID"],

        "source_title": r["SOURCE_TITLE"],

        "date_source": r.get("DATE_SOURCE"),

        "raw_text": r.get("RAW_TEXT"),

        "status": r["STATUS"],

        "error_message": r.get("ERROR_MESSAGE"),

        "import_type": r.get("IMPORT_TYPE"),

        "created_at": r["CREATED_AT"],
    }



def update_raw_content(
    id_raw: str,
    date_source: Optional[str],
    source_title: Optional[str],
    raw_text: Optional[str] = None,

    # 🔥 NEW
    content_type: Optional[str] = None,

    # 🔥 NEW
    id_primary_company: Optional[str] = None,
):

    client = get_bigquery_client()

    table_id = f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_CONTENT_RAW"

    query = f"""
        UPDATE `{table_id}`
        SET
            DATE_SOURCE = @date_source,

            SOURCE_TITLE = @source_title,

            RAW_TEXT = @raw_text,

            -- 🔥 NEW
            CONTENT_TYPE = @content_type,

            -- 🔥 NEW
            ID_PRIMARY_COMPANY = @id_primary_company

        WHERE ID_RAW = @id_raw
    """

    job_config = bigquery.QueryJobConfig(
        query_parameters=[

            bigquery.ScalarQueryParameter(
                "date_source",
                "DATE",
                date_source
            ),

            bigquery.ScalarQueryParameter(
                "source_title",
                "STRING",
                source_title
            ),

            bigquery.ScalarQueryParameter(
                "raw_text",
                "STRING",
                raw_text
            ),

            # 🔥 NEW
            bigquery.ScalarQueryParameter(
                "content_type",
                "STRING",
                content_type
            ),

            # 🔥 NEW
            bigquery.ScalarQueryParameter(
                "id_primary_company",
                "STRING",
                id_primary_company
            ),

            bigquery.ScalarQueryParameter(
                "id_raw",
                "STRING",
                id_raw
            ),
        ]
    )

    client.query(
        query,
        job_config=job_config
    ).result()

def get_raw_stats() -> dict:

    query = f"""
        SELECT

            COUNT(*) AS total,

            SUM(
                CASE WHEN STATUS = 'STORED'
                THEN 1 ELSE 0 END
            ) AS total_stored,

            SUM(
                CASE WHEN STATUS = 'PROCESSING'
                THEN 1 ELSE 0 END
            ) AS total_processing,

            SUM(
                CASE WHEN STATUS = 'ERROR'
                THEN 1 ELSE 0 END
            ) AS total_error,

            -- 🔥 NEW
            SUM(
                CASE WHEN COALESCE(CONTENT_TYPE, 'ANALYSIS') = 'NEWS'
                THEN 1 ELSE 0 END
            ) AS total_news,

            SUM(
                CASE WHEN COALESCE(CONTENT_TYPE, 'ANALYSIS') = 'ANALYSIS'
                THEN 1 ELSE 0 END
            ) AS total_analysis

        FROM `{TABLE_CONTENT_RAW}`
    """

    rows = query_bq(query)

    if not rows:
        return {
            "total": 0,
            "total_stored": 0,
            "total_processing": 0,
            "total_error": 0,

            # 🔥 NEW
            "total_news": 0,
            "total_analysis": 0,
        }

    r = rows[0]

    return {

        "total": r.get("total", 0),

        "total_stored": r.get("total_stored", 0),

        "total_processing": r.get("total_processing", 0),

        "total_error": r.get("total_error", 0),

        # 🔥 NEW
        "total_news": r.get("total_news", 0),

        "total_analysis": r.get("total_analysis", 0),
    }
# ============================================================
# SUBSTACK
# ============================================================

def raw_url_exists(url: str) -> bool:
    rows = query_bq(
        f"""
        SELECT 1
        FROM `{TABLE_CONTENT_RAW}`
        WHERE SOURCE_URL = @url
        LIMIT 1
        """,
        {"url": url},
    )
    return bool(rows)

def get_source_monitoring():

    from utils.bigquery_utils import query_bq

    query = """
    WITH ranked AS (

      SELECT
        r.SOURCE_ID,

        -- 🔥 NEW
        r.CONTENT_TYPE,

        r.DATE_SOURCE,
        r.SOURCE_URL,
        r.SOURCE_TITLE,

        ROW_NUMBER() OVER (
          PARTITION BY r.SOURCE_ID, r.CONTENT_TYPE
          ORDER BY r.DATE_SOURCE DESC
        ) AS rn

      FROM `adex-5555.RATECARD_PROD.RATECARD_CONTENT_RAW` r
    ),

    last_article AS (

      SELECT
        SOURCE_ID,

        -- 🔥 NEW
        CONTENT_TYPE,

        DATE_SOURCE AS LAST_ARTICLE_DATE,
        SOURCE_URL AS LAST_ARTICLE_URL,
        SOURCE_TITLE AS LAST_ARTICLE_TITLE

      FROM ranked

      WHERE rn = 1
    ),

    agg AS (

      SELECT
        SOURCE_ID,

        -- 🔥 NEW
        CONTENT_TYPE,

        MAX(CREATED_AT) AS LAST_IMPORT_AT,

        COUNTIF(
          CREATED_AT >= TIMESTAMP_SUB(
            CURRENT_TIMESTAMP(),
            INTERVAL 7 DAY
          )
        ) AS NB_IMPORTED_7D

      FROM `adex-5555.RATECARD_PROD.RATECARD_CONTENT_RAW`

      GROUP BY
        SOURCE_ID,
        CONTENT_TYPE
    )

    SELECT

      s.SOURCE_ID,

      s.NAME AS SOURCE_NAME,

      -- 🔥 NEW
      COALESCE(
        la.CONTENT_TYPE,
        agg.CONTENT_TYPE,
        'ANALYSIS'
      ) AS CONTENT_TYPE,

      la.LAST_ARTICLE_DATE,
      la.LAST_ARTICLE_URL,
      la.LAST_ARTICLE_TITLE,

      agg.LAST_IMPORT_AT,
      agg.NB_IMPORTED_7D

    FROM `adex-5555.RATECARD_PROD.RATECARD_SOURCE` s

    LEFT JOIN last_article la
      ON s.SOURCE_ID = la.SOURCE_ID

    LEFT JOIN agg
      ON s.SOURCE_ID = agg.SOURCE_ID
      AND COALESCE(la.CONTENT_TYPE, 'ANALYSIS')
          = COALESCE(agg.CONTENT_TYPE, 'ANALYSIS')

    ORDER BY agg.LAST_IMPORT_AT DESC
    """

    rows = query_bq(query)

    return rows

# ============================================================
# RESET RELATIONS
# ============================================================

def reset_and_insert(table, id_field, id_content, values):

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
    # CONTENT TYPE
    # ============================================================

    if data.content_type is not None:
        fields["CONTENT_TYPE"] = data.content_type

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

    # ============================================================
    # SUMMARY
    # ============================================================

    if data.title is not None:
        fields["TITLE"] = data.title.strip()

    if data.excerpt is not None:
        fields["EXCERPT"] = data.excerpt

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

    reset_and_insert(
        TABLE_CONTENT_EVENT,
        "ID_EVENT",
        id_content,
        data.events if data.events is not None else [],
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

    # ============================================================
    # PERSONS (gestion spécifique car rôle)
    # ============================================================

    client = get_bigquery_client()

    client.query(
        f"""
        DELETE FROM `{TABLE_CONTENT_PERSON}`
        WHERE ID_CONTENT = @id
        """,
        job_config=bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter(
                    "id",
                    "STRING",
                    id_content
                )
            ]
        ),
    ).result()

    if data.persons:

        insert_bq(
            TABLE_CONTENT_PERSON,
            [
                {
                    "ID_CONTENT": id_content,
                    "ID_PERSON": p.id_person,
                    "ROLE": p.role,
                    "CREATED_AT": now,
                }
                for p in data.persons
            ],
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


# ============================================================
# PUBLISH CONTENT
# ============================================================


def publish_content(
    id_content: str,
    published_at: Optional[datetime] = None,
):

    now_dt = datetime.now(timezone.utc)

    # ============================================================
    # 1️⃣ CHECK
    # ============================================================

    rows = query_bq(
        f"""
        SELECT
            STATUS,

            SOURCE_DATE,

            NUMBERS_PARSED,

            -- 🔥 NEW
            CONTENT_TYPE,

            -- 🔥 NEW
            ID_PRIMARY_COMPANY

        FROM `{TABLE_CONTENT}`

        WHERE ID_CONTENT = @id_content
        """,
        {"id_content": id_content}
    )

    if not rows:
        raise ValueError("Content introuvable")

    current_status = rows[0]["STATUS"]

    source_date = rows[0]["SOURCE_DATE"]

    numbers_parsed = rows[0].get("NUMBERS_PARSED")

    # 🔥 NEW
    content_type = (
        rows[0].get("CONTENT_TYPE")
        or "ANALYSIS"
    )

    # 🔥 NEW
    id_primary_company = rows[0].get(
        "ID_PRIMARY_COMPANY"
    )

    if current_status != "READY":
        raise ValueError("Content must be READY before publish")

    # ============================================================
    # 2️⃣ DATE
    # ============================================================

    if published_at is None:
        published_at = source_date or now_dt

    if (
        isinstance(published_at, date)
        and not isinstance(published_at, datetime)
    ):

        published_at = datetime.combine(
            published_at,
            datetime.min.time(),
            tzinfo=timezone.utc
        )

    elif (
        isinstance(published_at, datetime)
        and published_at.tzinfo is None
    ):

        published_at = published_at.replace(
            tzinfo=timezone.utc
        )

    # ============================================================
    # 3️⃣ STATUS
    # ============================================================

    status = (
        "PUBLISHED"
        if published_at <= now_dt
        else "SCHEDULED"
    )

    # ============================================================
    # 4️⃣ UPDATE CONTENT
    # ============================================================

    update_bq(
        table=TABLE_CONTENT,
        fields={
            "STATUS": status,
            "PUBLISHED_AT": published_at,
            "UPDATED_AT": now_dt,
        },
        where={"ID_CONTENT": id_content},
    )

    print(
        "🚀 CONTENT PUBLISHED:",
        {
            "id_content": id_content,
            "status": status,
            "content_type": content_type,
            "id_primary_company": id_primary_company,
        }
    )

    # ============================================================
    # 5️⃣ AFTER PUBLISH SYNC
    # ============================================================

    if status == "PUBLISHED":

        try:

            after_publish_sync(
                id_content=id_content,
            )

        except Exception as e:

            print(
                "❌ AFTER PUBLISH SYNC ERROR:",
                str(e)
            )

    # ============================================================
    # 🔥 NEWS → PAS DE PIPELINE NUMBERS
    # ============================================================

    if content_type == "NEWS":

        print(
            "ℹ️ NEWS CONTENT → SKIP NUMBERS BACKLOG:",
            id_content
        )

        return status

    # ============================================================
    # 6️⃣ BACKLOG NUMBERS
    # ============================================================

    if status == "PUBLISHED":

        if numbers_parsed:

            print(
                "⏭️ Skip parsing (already processed):",
                id_content
            )

            return status

        try:

            print(
                "📊 Parsing numbers for content:",
                id_content
            )

            backlog_rows = get_numbers_from_content(
                id_content
            )

            if not backlog_rows:

                print("ℹ️ No valid numbers found")

                return status

            processed_results = []

            for backlog_row in backlog_rows:

                result = process_backlog_row(
                    backlog_row
                )

                if result.get("status") == "ok":

                    processed_results.append(result)

            if processed_results:

                insert_backlog_batch(
                    processed_results
                )

                print(
                    f"✅ {len(processed_results)} backlog numbers inserted"
                )

            else:

                print("ℹ️ No valid backlog results")

            update_bq(
                table=TABLE_CONTENT,
                fields={
                    "NUMBERS_PARSED": True,
                    "UPDATED_AT": now_dt,
                },
                where={"ID_CONTENT": id_content},
            )

        except Exception as e:

            print(
                "❌ BACKLOG ERROR:",
                str(e)
            )

            return status

    return status

def mark_content_ready(id_content: str):

    rows = query_bq(
        f"""
        SELECT STATUS
        FROM `{TABLE_CONTENT}`
        WHERE ID_CONTENT = @id_content
        """,
        {"id_content": id_content}
    )

    if not rows:
        raise ValueError("Content introuvable")

    current_status = rows[0]["STATUS"]

    if current_status == "READY":
        # Déjà ready → OK
        return

    if current_status not in ["DRAFT"]:
        raise ValueError(f"Cannot mark READY from status {current_status}")

    update_bq(
        TABLE_CONTENT,
        {
            "STATUS": "READY",
            "UPDATED_AT": datetime.utcnow().isoformat()
        },
        where={"ID_CONTENT": id_content}
    )

def bulk_ready(ids: list[str]) -> int:

    if not ids:
        return 0

    now = datetime.now(timezone.utc)

    query = f"""
        UPDATE `{TABLE_CONTENT}`
        SET
            STATUS = 'READY',
            UPDATED_AT = @now
        WHERE
            STATUS = 'DRAFT'
            AND ID_CONTENT IN UNNEST(@ids)
    """

    query_bq(
        query,
        {
            "ids": ids,
            "now": now,
        },
    )

    return len(ids)


def bulk_publish(ids: List[str]) -> Dict[str, int]:

    if not ids:
        return {"updated": 0, "skipped": 0}

    updated = 0
    skipped = 0

    for id_content in ids:
        try:
            publish_content(id_content)
            updated += 1
        except Exception:
            skipped += 1

    return {
        "updated": updated,
        "skipped": skipped,
    }

# ============================================================
# CONTENT STATS
# ============================================================

def get_content_stats():

    sql = f"""
        SELECT

          COUNT(*) AS TOTAL,

          COUNTIF(
            STATUS = 'DRAFT'
          ) AS TOTAL_DRAFT,

          COUNTIF(
            STATUS = 'READY'
          ) AS TOTAL_READY,

          COUNTIF(
            STATUS = 'PUBLISHED'
          ) AS TOTAL_PUBLISHED,

          COUNTIF(
            STATUS = 'SCHEDULED'
          ) AS TOTAL_SCHEDULED,

          -- 🔥 NEW
          COUNTIF(
            COALESCE(CONTENT_TYPE, 'ANALYSIS') = 'NEWS'
          ) AS TOTAL_NEWS,

          COUNTIF(
            COALESCE(CONTENT_TYPE, 'ANALYSIS') = 'ANALYSIS'
          ) AS TOTAL_ANALYSIS,

          COUNTIF(
            STATUS = 'PUBLISHED'
            AND EXTRACT(YEAR FROM PUBLISHED_AT)
                = EXTRACT(YEAR FROM CURRENT_DATE())
          ) AS TOTAL_PUBLISHED_THIS_YEAR,

          COUNTIF(
            STATUS = 'PUBLISHED'
            AND EXTRACT(YEAR FROM PUBLISHED_AT)
                = EXTRACT(YEAR FROM CURRENT_DATE())
            AND EXTRACT(MONTH FROM PUBLISHED_AT)
                = EXTRACT(MONTH FROM CURRENT_DATE())
          ) AS TOTAL_PUBLISHED_THIS_MONTH

        FROM `{TABLE_CONTENT}`
    """

    rows = query_bq(sql)

    if not rows:

        return {
            "total": 0,
            "total_draft": 0,
            "total_ready": 0,
            "total_published": 0,
            "total_scheduled": 0,

            # 🔥 NEW
            "total_news": 0,
            "total_analysis": 0,

            "total_published_this_year": 0,
            "total_published_this_month": 0,
        }

    r = rows[0]

    return {

        "total": r.get("TOTAL", 0),

        "total_draft": r.get("TOTAL_DRAFT", 0),

        "total_ready": r.get("TOTAL_READY", 0),

        "total_published": r.get("TOTAL_PUBLISHED", 0),

        "total_scheduled": r.get("TOTAL_SCHEDULED", 0),

        # 🔥 NEW
        "total_news": r.get("TOTAL_NEWS", 0),

        "total_analysis": r.get("TOTAL_ANALYSIS", 0),

        "total_published_this_year": r.get(
            "TOTAL_PUBLISHED_THIS_YEAR",
            0
        ),

        "total_published_this_month": r.get(
            "TOTAL_PUBLISHED_THIS_MONTH",
            0
        ),
    }

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
