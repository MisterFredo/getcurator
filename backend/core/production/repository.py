import json

from typing import Any

from config import (
    BQ_DATASET,
    BQ_PROJECT,
)

from core.production.models import (
    ProductionPreparedCorpus,
)

from utils.bigquery_utils import (
    query_bq,
)


TABLE_PRODUCTION = (
    f"{BQ_PROJECT}.{BQ_DATASET}."
    "RATECARD_PRODUCTION"
)


# ============================================================
# HELPERS
# ============================================================

def _normalize_production_id(
    production_id: str,
) -> str:
    normalized = (
        production_id or ""
    ).strip()

    if not normalized:
        raise ValueError(
            "Identifiant de production vide."
        )

    return normalized


def _read_json(value: Any) -> Any:
    if isinstance(value, str):
        return json.loads(value)

    return value


def _timestamp_out(value: Any) -> str | None:
    if value is None:
        return None

    if hasattr(value, "isoformat"):
        return value.isoformat()

    return str(value)


def _metadata_out(row: dict) -> dict:
    return {
        "production_id": (
            row["PRODUCTION_ID"]
        ),
        "status": row["STATUS"],
        "title": row["TITLE"],
        "output_language": (
            row["OUTPUT_LANGUAGE"]
        ),
        "output_format": (
            row["OUTPUT_FORMAT"]
        ),
        "target_page_count": (
            row["TARGET_PAGE_COUNT"]
        ),
        "created_at": _timestamp_out(
            row["CREATED_AT"]
        ),
        "updated_at": _timestamp_out(
            row["UPDATED_AT"]
        ),
        "corpus_sha256": (
            row["CORPUS_SHA256"]
        ),
    }


# ============================================================
# GET PRODUCTION
# ============================================================

def get_production(
    production_id: str,
) -> dict | None:
    production_id = (
        _normalize_production_id(
            production_id
        )
    )

    rows = query_bq(
        f"""
        SELECT
          PRODUCTION_ID,
          STATUS,
          TITLE,
          OUTPUT_LANGUAGE,
          OUTPUT_FORMAT,
          TARGET_PAGE_COUNT,
          CREATED_AT,
          UPDATED_AT,
          CORPUS_SHA256,
          CORPUS_JSON

        FROM `{TABLE_PRODUCTION}`

        WHERE PRODUCTION_ID = @production_id

        LIMIT 2
        """,
        {
            "production_id": production_id,
        },
    ) or []

    if not rows:
        return None

    if len(rows) > 1:
        raise ValueError(
            "Plusieurs lignes existent pour "
            f"la production {production_id}."
        )

    row = rows[0]

    corpus = (
        ProductionPreparedCorpus.model_validate(
            _read_json(
                row["CORPUS_JSON"]
            )
        )
    )

    if (
        corpus.production_id
        != row["PRODUCTION_ID"]
        or corpus.corpus_sha256
        != row["CORPUS_SHA256"]
    ):
        raise ValueError(
            "Métadonnées incohérentes pour "
            f"la production {production_id}."
        )

    return {
        **_metadata_out(row),
        "corpus": corpus.model_dump(
            mode="json",
        ),
    }


# ============================================================
# SAVE INITIAL CORPUS
# ============================================================

def save_prepared_production(
    corpus: ProductionPreparedCorpus,
) -> dict:
    """
    Insert an initial production snapshot.

    Never replace the corpus of an existing production.
    Repeated saves of the same ID and corpus hash return
    the first persisted snapshot.
    """

    production_id = (
        _normalize_production_id(
            corpus.production_id
        )
    )

    request = corpus.request

    query_bq(
        f"""
        MERGE `{TABLE_PRODUCTION}` AS target

        USING (
          SELECT
            @production_id AS PRODUCTION_ID,
            @status AS STATUS,
            @title AS TITLE,
            @output_language AS OUTPUT_LANGUAGE,
            @output_format AS OUTPUT_FORMAT,
            @target_page_count AS TARGET_PAGE_COUNT,
            @corpus_sha256 AS CORPUS_SHA256,
            PARSE_JSON(
              @corpus_json
            ) AS CORPUS_JSON
        ) AS source

        ON
          target.PRODUCTION_ID =
            source.PRODUCTION_ID

        WHEN NOT MATCHED THEN

          INSERT (
            PRODUCTION_ID,
            STATUS,
            TITLE,
            OUTPUT_LANGUAGE,
            OUTPUT_FORMAT,
            TARGET_PAGE_COUNT,
            CREATED_AT,
            UPDATED_AT,
            CORPUS_SHA256,
            CORPUS_JSON
          )

          VALUES (
            source.PRODUCTION_ID,
            source.STATUS,
            source.TITLE,
            source.OUTPUT_LANGUAGE,
            source.OUTPUT_FORMAT,
            source.TARGET_PAGE_COUNT,
            CURRENT_TIMESTAMP(),
            CURRENT_TIMESTAMP(),
            source.CORPUS_SHA256,
            source.CORPUS_JSON
          )
        """,
        {
            "production_id": production_id,
            "status": "CORPUS_PREPARED",
            "title": request.title,
            "output_language": (
                request.output_language
            ),
            "output_format": (
                request.output_format
            ),
            "target_page_count": (
                request.target_page_count
            ),
            "corpus_sha256": (
                corpus.corpus_sha256
            ),
            "corpus_json": (
                corpus.model_dump_json()
            ),
        },
    )

    saved = get_production(
        production_id=production_id,
    )

    if saved is None:
        raise RuntimeError(
            "La production est introuvable "
            "après son enregistrement."
        )

    if (
        saved["corpus_sha256"]
        != corpus.corpus_sha256
    ):
        raise ValueError(
            "Cet identifiant de production "
            "correspond déjà à un autre socle."
        )

    return saved


# ============================================================
# LIST PRODUCTIONS
# ============================================================

def list_productions(
    limit: int = 20,
    offset: int = 0,
) -> list[dict]:
    safe_limit = min(
        max(limit, 1),
        100,
    )

    safe_offset = max(
        offset,
        0,
    )

    rows = query_bq(
        f"""
        SELECT
          PRODUCTION_ID,
          STATUS,
          TITLE,
          OUTPUT_LANGUAGE,
          OUTPUT_FORMAT,
          TARGET_PAGE_COUNT,
          CREATED_AT,
          UPDATED_AT,
          CORPUS_SHA256

        FROM `{TABLE_PRODUCTION}`

        ORDER BY
          CREATED_AT DESC,
          PRODUCTION_ID DESC

        LIMIT @limit
        OFFSET @offset
        """,
        {
            "limit": safe_limit,
            "offset": safe_offset,
        },
    ) or []

    return [
        _metadata_out(row)
        for row in rows
    ]
