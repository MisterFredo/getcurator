import uuid
from datetime import datetime

from google.cloud import bigquery

from config import BQ_PROJECT, BQ_DATASET
from utils.bigquery_utils import (
    query_bq,
    update_bq,
    get_bigquery_client,
)

from api.source.models import SourceCreate, SourceUpdate


TABLE_SOURCE = f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_SOURCE"
TABLE_SOURCE_UNIVERSE = f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_SOURCE_UNIVERSE"


# ============================================================
# CREATE SOURCE
# ============================================================
def create_source(data: SourceCreate) -> str:

    source_id = str(uuid.uuid4())
    now = datetime.utcnow().isoformat()

    row = [{
        "SOURCE_ID": source_id,
        "NAME": data.name,
        "TYPE_SOURCE": data.type_source,
        "DESCRIPTION": data.description,
        "DOMAIN": data.domain,
        "AUTHOR": data.author,
        "AUTHOR_PROFILE": data.author_profile,
        "LOGO": None,
        "ACQUISITION_MODE": data.acquisition_mode,
        "CREATED_AT": now,
    }]

    client = get_bigquery_client()

    client.load_table_from_json(
        row,
        TABLE_SOURCE,
        job_config=bigquery.LoadJobConfig(
            write_disposition="WRITE_APPEND"
        ),
    ).result()

    # ============================================================
    # 🔥 INSERT UNIVERSE (si fourni)
    # ============================================================

    if getattr(data, "universe_id", None):

        universe_row = [{
            "ID_SOURCE": source_id,
            "ID_UNIVERSE": data.universe_id,
            "CREATED_AT": now,
        }]

        client.load_table_from_json(
            universe_row,
            TABLE_SOURCE_UNIVERSE,
            job_config=bigquery.LoadJobConfig(
                write_disposition="WRITE_APPEND"
            ),
        ).result()

    return source_id


# ============================================================
# LIST SOURCES (snake_case contractuel)
# ============================================================
def list_sources():

    sql = f"""
        SELECT
            s.SOURCE_ID,
            s.NAME,
            s.TYPE_SOURCE,
            s.DESCRIPTION,
            s.DOMAIN,
            s.AUTHOR,
            s.AUTHOR_PROFILE,
            s.LOGO,
            s.ACQUISITION_MODE,
            s.CREATED_AT,
            su.ID_UNIVERSE
        FROM `{TABLE_SOURCE}` s
        LEFT JOIN `{TABLE_SOURCE_UNIVERSE}` su
        ON s.SOURCE_ID = su.ID_SOURCE
        ORDER BY s.NAME ASC
    """

    rows = query_bq(sql)

    return [
        {
            "source_id": r["SOURCE_ID"],
            "name": r["NAME"],
            "type_source": r["TYPE_SOURCE"],
            "description": r["DESCRIPTION"],
            "domain": r["DOMAIN"],
            "author": r["AUTHOR"],
            "author_profile": r["AUTHOR_PROFILE"],
            "logo": r.get("LOGO"),
            "acquisition_mode": r.get("ACQUISITION_MODE"),
            "created_at": r["CREATED_AT"],
            "universe_id": r.get("ID_UNIVERSE"),
        }
        for r in rows
    ]

# ============================================================
# GET ONE SOURCE (snake_case contractuel)
# ============================================================
def get_source(source_id: str):

    sql = f"""
        SELECT
            s.SOURCE_ID,
            s.NAME,
            s.TYPE_SOURCE,
            s.DESCRIPTION,
            s.DOMAIN,
            s.AUTHOR,
            s.AUTHOR_PROFILE,
            s.LOGO,
            s.ACQUISITION_MODE,
            s.CREATED_AT,
            su.ID_UNIVERSE
        FROM `{TABLE_SOURCE}` s
        LEFT JOIN `{TABLE_SOURCE_UNIVERSE}` su
        ON s.SOURCE_ID = su.ID_SOURCE
        WHERE s.SOURCE_ID = @id
        LIMIT 1
    """

    rows = query_bq(sql, {"id": source_id})

    if not rows:
        return None

    r = rows[0]

    return {
        "source_id": r["SOURCE_ID"],
        "name": r["NAME"],
        "type_source": r["TYPE_SOURCE"],
        "description": r["DESCRIPTION"],
        "domain": r["DOMAIN"],
        "author": r["AUTHOR"],
        "author_profile": r["AUTHOR_PROFILE"],
        "logo": r.get("LOGO"),
        "acquisition_mode": r.get("ACQUISITION_MODE"),
        "created_at": r["CREATED_AT"],
        "universe_id": r.get("ID_UNIVERSE"),
    }
# ============================================================
# UPDATE SOURCE
# ============================================================
def update_source(source_id: str, data: SourceUpdate) -> bool:

    values = data.dict(exclude_unset=True)

    if not values:
        return False

    mapping = {
        "name": "NAME",
        "type_source": "TYPE_SOURCE",
        "description": "DESCRIPTION",
        "domain": "DOMAIN",
        "author": "AUTHOR",
        "author_profile": "AUTHOR_PROFILE",
        "acquisition_mode": "ACQUISITION_MODE",
        "logo": "LOGO",
    }

    # ============================================================
    # UPDATE TABLE SOURCE
    # ============================================================

    bq_values = {
        mapping[k]: v
        for k, v in values.items()
        if k in mapping
    }

    updated = False

    if bq_values:
        updated = update_bq(
            table=TABLE_SOURCE,
            fields=bq_values,
            where={"SOURCE_ID": source_id},
        )

    # ============================================================
    # 🔥 UPDATE UNIVERSE
    # ============================================================

    if "universe_id" in values:

        # delete existing mapping
        query_bq(
            f"""
            DELETE FROM `{TABLE_SOURCE_UNIVERSE}`
            WHERE ID_SOURCE = @id
            """,
            {"id": source_id},
        )

        # insert new mapping if provided
        if values["universe_id"]:
            query_bq(
                f"""
                INSERT INTO `{TABLE_SOURCE_UNIVERSE}` (
                    ID_SOURCE,
                    ID_UNIVERSE,
                    CREATED_AT
                )
                VALUES (@id, @universe, CURRENT_TIMESTAMP())
                """,
                {
                    "id": source_id,
                    "universe": values["universe_id"],
                },
            )

        updated = True

    return updated

def delete_source(source_id: str) -> bool:

    # ============================================================
    # CHECK EXISTENCE
    # ============================================================

    existing = query_bq(
        f"""
        SELECT SOURCE_ID
        FROM `{TABLE_SOURCE}`
        WHERE SOURCE_ID = @id
        """,
        {"id": source_id},
    )

    if not existing:
        return False

    # ============================================================
    # DELETE UNIVERSE MAPPING
    # ============================================================

    query_bq(
        f"""
        DELETE FROM `{TABLE_SOURCE_UNIVERSE}`
        WHERE ID_SOURCE = @id
        """,
        {"id": source_id},
    )

    # ============================================================
    # DELETE SOURCE
    # ============================================================

    query_bq(
        f"""
        DELETE FROM `{TABLE_SOURCE}`
        WHERE SOURCE_ID = @id
        """,
        {"id": source_id},
    )

    return True
