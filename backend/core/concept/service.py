import uuid
from datetime import datetime
from google.cloud import bigquery

from config import BQ_PROJECT, BQ_DATASET
from utils.bigquery_utils import (
    query_bq,
    update_bq,
    get_bigquery_client,
)
from api.concept.models import (
    ConceptCreate,
    ConceptUpdate,
)

TABLE_CONCEPT = (
    f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_CONCEPT"
)


# ============================================================
# CREATE
# ============================================================

def create_concept(data: ConceptCreate) -> str:

    concept_id = str(uuid.uuid4())
    now = datetime.utcnow().isoformat()

    row = [{
        "ID_CONCEPT": concept_id,
        "LABEL": data.label,
        "DESCRIPTION": data.description or None,
        "IS_ACTIVE": True,
        "CREATED_AT": now,
        "UPDATED_AT": now,
    }]

    client = get_bigquery_client()

    client.load_table_from_json(
        row,
        TABLE_CONCEPT,
        job_config=bigquery.LoadJobConfig(
            write_disposition="WRITE_APPEND",
        ),
    ).result()

    return concept_id


# ============================================================
# LIST
# ============================================================

def list_concepts():

    sql = f"""
    SELECT
        ID_CONCEPT,
        LABEL,
        DESCRIPTION,
        CREATED_AT,
        UPDATED_AT
    FROM `{TABLE_CONCEPT}`
    WHERE COALESCE(IS_ACTIVE, TRUE)=TRUE
    ORDER BY UPPER(LABEL)
    """

    rows = query_bq(sql)

    return [
        {
            "id_concept": r["ID_CONCEPT"],
            "label": r["LABEL"],
            "description": r.get("DESCRIPTION"),
            "created_at": r.get("CREATED_AT"),
            "updated_at": r.get("UPDATED_AT"),
        }
        for r in rows
    ]


# ============================================================
# GET ONE
# ============================================================

def get_concept(concept_id: str):

    rows = query_bq(
        f"""
        SELECT
            ID_CONCEPT,
            LABEL,
            DESCRIPTION,
            CREATED_AT,
            UPDATED_AT
        FROM `{TABLE_CONCEPT}`
        WHERE ID_CONCEPT=@id
        LIMIT 1
        """,
        {
            "id": concept_id,
        },
    )

    if not rows:
        return None

    r = rows[0]

    return {
        "id_concept": r["ID_CONCEPT"],
        "label": r["LABEL"],
        "description": r.get("DESCRIPTION"),
        "created_at": r.get("CREATED_AT"),
        "updated_at": r.get("UPDATED_AT"),
    }


# ============================================================
# UPDATE
# ============================================================

def update_concept(
    id_concept: str,
    data: ConceptUpdate,
) -> bool:

    values = data.dict(
        exclude_unset=True,
    )

    if not values:
        return False

    mapping = {
        "label": "LABEL",
        "description": "DESCRIPTION",
        "is_active": "IS_ACTIVE",
    }

    bq_values = {
        mapping[k]: v
        for k, v in values.items()
        if k in mapping
    }

    if not bq_values:
        return False

    bq_values["UPDATED_AT"] = (
        datetime.utcnow().isoformat()
    )

    return update_bq(
        table=TABLE_CONCEPT,
        fields=bq_values,
        where={
            "ID_CONCEPT": id_concept,
        },
    )


# ============================================================
# DELETE
# ============================================================

def delete_concept(
    id_concept: str,
) -> bool:

    existing = query_bq(
        f"""
        SELECT ID_CONCEPT
        FROM `{TABLE_CONCEPT}`
        WHERE ID_CONCEPT=@id
        """,
        {
            "id": id_concept,
        },
    )

    if not existing:
        return False

    return update_bq(
        table=TABLE_CONCEPT,
        fields={
            "IS_ACTIVE": False,
            "UPDATED_AT": datetime.utcnow().isoformat(),
        },
        where={
            "ID_CONCEPT": id_concept,
        },
    )
