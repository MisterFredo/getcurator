# backend/core/knowledge/entity_service.py

from config import (
    BQ_PROJECT,
    BQ_DATASET,
)

from utils.bigquery_utils import (
    query_bq,
)

from .models import (
    KnowledgeEntityType,
)

from pydantic import (
    BaseModel,
)


# ============================================================
# MODEL
# ============================================================

class Entity(BaseModel):

    id: str

    name: str

    type: KnowledgeEntityType


# ============================================================
# TABLES
# ============================================================

TABLE_COMPANY = (
    f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_COMPANY"
)

TABLE_TOPIC = (
    f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_TOPIC"
)

TABLE_SOLUTION = (
    f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_SOLUTION"
)


# ============================================================
# GET ENTITY
# ============================================================

def get_entity(
    entity_type: KnowledgeEntityType,
    entity_id: str,
) -> Entity | None:

    match entity_type:

        case "company":

            return _get_entity(

                table=TABLE_COMPANY,

                id_column="ID_COMPANY",

                name_column="NAME",

                entity_type=entity_type,

                entity_id=entity_id,

            )

        case "topic":

            return _get_entity(

                table=TABLE_TOPIC,

                id_column="ID_TOPIC",

                name_column="LABEL",

                entity_type=entity_type,

                entity_id=entity_id,

            )

        case "solution":

            return _get_entity(

                table=TABLE_SOLUTION,

                id_column="ID_SOLUTION",

                name_column="NAME",

                entity_type=entity_type,

                entity_id=entity_id,

            )

    return None


# ============================================================
# GENERIC
# ============================================================

def _get_entity(
    table: str,
    id_column: str,
    name_column: str,
    entity_type: KnowledgeEntityType,
    entity_id: str,
) -> Entity | None:

    rows = query_bq(

        f"""
        SELECT

            {id_column} AS ID,

            {name_column} AS NAME

        FROM `{table}`

        WHERE

            {id_column} = @entity_id
        """,

        {
            "entity_id": entity_id,
        },

    )

    if not rows:
        return None

    row = rows[0]

    return Entity(

        id=row["ID"],

        name=row["NAME"],

        type=entity_type,

    )
