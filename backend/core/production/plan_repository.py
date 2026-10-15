import json

from uuid import uuid4

from config import (
    BQ_DATASET,
    BQ_PROJECT,
)

from core.production.models import (
    ProductionPlanSnapshot,
    ProductionPreparedCorpus,
)

from core.production.plan_service import (
    validate_production_plan,
)

from core.production.repository import (
    get_production,
)

from utils.bigquery_utils import (
    query_bq,
)


TABLE_PRODUCTION = (
    f"{BQ_PROJECT}.{BQ_DATASET}."
    "RATECARD_PRODUCTION"
)

TABLE_PLAN = (
    f"{BQ_PROJECT}.{BQ_DATASET}."
    "RATECARD_PRODUCTION_PLAN"
)


# ============================================================
# HELPERS
# ============================================================

def _read_json(value):
    if isinstance(value, str):
        return json.loads(value)

    return value


def _metadata_out(row: dict) -> dict:
    created_at = row["CREATED_AT"]

    return {
        "plan_id": row["PLAN_ID"],
        "production_id": (
            row["PRODUCTION_ID"]
        ),
        "plan_version": (
            row["PLAN_VERSION"]
        ),
        "corpus_sha256": (
            row["CORPUS_SHA256"]
        ),
        "created_at": (
            created_at.isoformat()
            if hasattr(
                created_at,
                "isoformat",
            )
            else str(created_at)
        ),
    }


def _plan_out(row: dict) -> dict:
    snapshot = (
        ProductionPlanSnapshot.model_validate(
            _read_json(
                row["PLAN_JSON"]
            )
        )
    )

    if (
        snapshot.production_id
        != row["PRODUCTION_ID"]
        or snapshot.corpus_sha256
        != row["CORPUS_SHA256"]
    ):
        raise ValueError(
            "Les métadonnées du plan "
            "sont incohérentes."
        )

    return {
        **_metadata_out(row),
        "snapshot": snapshot.model_dump(
            mode="json",
        ),
    }


# ============================================================
# SAVE A NEW PLAN VERSION
# ============================================================

def save_production_plan(
    snapshot: ProductionPlanSnapshot,
) -> dict:
    production = get_production(
        production_id=(
            snapshot.production_id
        ),
    )

    if production is None:
        raise ValueError(
            "Production introuvable."
        )

    if (
        production["corpus_sha256"]
        != snapshot.corpus_sha256
    ):
        raise ValueError(
            "Le plan ne correspond pas "
            "au socle enregistré."
        )

    corpus = (
        ProductionPreparedCorpus.model_validate(
            production["corpus"]
        )
    )

    validate_production_plan(
        plan=snapshot.plan,
        corpus=corpus,
    )

    plan_id = str(uuid4())

    # Allocate the version and insert its snapshot
    # in the same transaction.
    query_bq(
        f"""
        BEGIN TRANSACTION;

        UPDATE `{TABLE_PRODUCTION}`

        SET
          PLAN_VERSION =
            COALESCE(PLAN_VERSION, 0) + 1,

          STATUS = 'PLAN_TO_REVIEW',

          UPDATED_AT = CURRENT_TIMESTAMP()

        WHERE
          PRODUCTION_ID = @production_id
          AND CORPUS_SHA256 = @corpus_sha256
          AND STATUS IN (
            'CORPUS_PREPARED',
            'PLAN_TO_REVIEW'
          );

        ASSERT @@row_count = 1
          AS 'Production unavailable or incompatible state';

        INSERT INTO `{TABLE_PLAN}`
        (
          PLAN_ID,
          PRODUCTION_ID,
          PLAN_VERSION,
          CORPUS_SHA256,
          CREATED_AT,
          PLAN_JSON
        )

        SELECT
          @plan_id,
          PRODUCTION_ID,
          PLAN_VERSION,
          CORPUS_SHA256,
          CURRENT_TIMESTAMP(),
          PARSE_JSON(@plan_json)

        FROM `{TABLE_PRODUCTION}`

        WHERE PRODUCTION_ID = @production_id;

        ASSERT @@row_count = 1
          AS 'Invalid plan insertion';

        COMMIT TRANSACTION;
        """,
        {
            "production_id": (
                snapshot.production_id
            ),
            "corpus_sha256": (
                snapshot.corpus_sha256
            ),
            "plan_id": plan_id,
            "plan_json": (
                snapshot.model_dump_json()
            ),
        },
    )

    rows = query_bq(
        f"""
        SELECT
          PLAN_ID,
          PRODUCTION_ID,
          PLAN_VERSION,
          CORPUS_SHA256,
          CREATED_AT,
          PLAN_JSON

        FROM `{TABLE_PLAN}`

        WHERE
          PRODUCTION_ID = @production_id
          AND PLAN_ID = @plan_id

        LIMIT 2
        """,
        {
            "production_id": (
                snapshot.production_id
            ),
            "plan_id": plan_id,
        },
    ) or []

    if len(rows) != 1:
        raise RuntimeError(
            "Impossible de relire "
            "le plan enregistré."
        )

    return _plan_out(rows[0])


# ============================================================
# GET LATEST OR SPECIFIC PLAN VERSION
# ============================================================

def get_production_plan(
    production_id: str,
    version: int | None = None,
) -> dict | None:
    if version is not None and version < 1:
        raise ValueError(
            "La version du plan doit "
            "être supérieure à zéro."
        )

    rows = query_bq(
        f"""
        SELECT
          PLAN_ID,
          PRODUCTION_ID,
          PLAN_VERSION,
          CORPUS_SHA256,
          CREATED_AT,
          PLAN_JSON

        FROM `{TABLE_PLAN}`

        WHERE
          PRODUCTION_ID = @production_id
          AND (
            @version = 0
            OR PLAN_VERSION = @version
          )

        ORDER BY
          PLAN_VERSION DESC,
          CREATED_AT DESC

        LIMIT 1
        """,
        {
            "production_id": production_id,
            "version": (
                version
                if version is not None
                else 0
            ),
        },
    ) or []

    if not rows:
        return None

    return _plan_out(rows[0])


# ============================================================
# LIST PLAN VERSIONS WITHOUT THEIR FULL CONTENT
# ============================================================

def list_production_plans(
    production_id: str,
    limit: int = 20,
    offset: int = 0,
) -> list[dict]:
    rows = query_bq(
        f"""
        SELECT
          PLAN_ID,
          PRODUCTION_ID,
          PLAN_VERSION,
          CORPUS_SHA256,
          CREATED_AT

        FROM `{TABLE_PLAN}`

        WHERE PRODUCTION_ID = @production_id

        ORDER BY PLAN_VERSION DESC

        LIMIT @limit
        OFFSET @offset
        """,
        {
            "production_id": production_id,
            "limit": min(
                max(limit, 1),
                100,
            ),
            "offset": max(
                offset,
                0,
            ),
        },
    ) or []

    return [
        _metadata_out(row)
        for row in rows
    ]
