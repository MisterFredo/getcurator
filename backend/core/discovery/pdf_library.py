
"""PDF Studio V8 — Persistent documentary library.

Import evidence units and editorial topics into BigQuery.
No LLM calls. No RAW content creation.
"""

from __future__ import annotations

import json
import uuid

from google.cloud import bigquery

from config import BQ_PROJECT, BQ_DATASET
from utils.bigquery_utils import get_bigquery_client


BASE = f"{BQ_PROJECT}.{BQ_DATASET}"

DOCUMENT = f"{BASE}.RATECARD_SOURCE_DOCUMENT"
UNIT = f"{BASE}.RATECARD_DOCUMENT_UNIT"
TOPIC = f"{BASE}.RATECARD_DOCUMENT_TOPIC"
LINK = f"{BASE}.RATECARD_DOCUMENT_TOPIC_UNIT"


def _required(value, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label} obligatoire.")
    return value.strip()


def _optional(value):
    return str(value).strip() if value is not None else None


def _query(client, sql, params=None):
    return list(
        client.query(
            sql,
            job_config=bigquery.QueryJobConfig(
                query_parameters=params or [],
            ),
        ).result()
    )


def _document(client, document_id: str):
    rows = _query(
        client,
        f"""
        SELECT ID_DOCUMENT, ID_SOURCE, SHA256, PAGE_COUNT
        FROM `{DOCUMENT}`
        WHERE ID_DOCUMENT = @id
        LIMIT 1
        """,
        [
            bigquery.ScalarQueryParameter(
                "id", "STRING", document_id
            )
        ],
    )

    if not rows:
        raise ValueError(
            "Document non enregistré dans "
            "RATECARD_SOURCE_DOCUMENT."
        )

    return rows[0]


def _normalize(payload: dict):
    if not isinstance(payload, dict):
        raise ValueError("Payload invalide.")

    if payload.get("version") != "8.0":
        raise ValueError("Export PDF Studio V8 requis.")

    if payload.get("extraction_complete") is not True:
        raise ValueError(
            "Extraction documentaire incomplète."
        )

    units = payload.get("units")
    topics = payload.get("topics")

    if not isinstance(units, list) or not units:
        raise ValueError("Liste units absente ou vide.")

    if not isinstance(topics, dict):
        raise ValueError("Objet topics manquant.")

    if topics.get("version") != "8.0":
        raise ValueError("Consolidation V8 requise.")

    proposals = topics.get("proposals")

    if not isinstance(proposals, list) or not proposals:
        raise ValueError("Aucun sujet consolidé.")

    unit_rows = []
    topic_rows = []
    link_rows = []

    unit_ids = set()
    topic_ids = set()

    for unit in units:
        if not isinstance(unit, dict):
            raise ValueError("Information invalide.")

        uid = _required(unit.get("id"), "unit.id")

        if uid in unit_ids:
            raise ValueError(f"Unit dupliquée : {uid}")

        unit_ids.add(uid)

        page = unit.get("page")

        if type(page) is not int or page < 1:
            raise ValueError(
                f"Page invalide pour {uid}."
            )

        status = _required(
            unit.get("status"), "unit.status"
        )

        if status not in {
            "VERIFIED", "NEEDS_REVIEW", "REJECTED"
        }:
            raise ValueError(
                f"Statut invalide pour {uid}."
            )

        unit_rows.append({
            "UNIT_ID": uid,
            "PDF_PAGE": page,
            "FACT": _required(
                unit.get("fact"), f"{uid}.fact"
            ),
            "QUOTE": _optional(unit.get("quote")) or "",
            "VERIFICATION_STATUS": status,
            "KIND": _optional(unit.get("kind")),
            "GEOGRAPHY": _optional(unit.get("geography")),
            "PERIOD": _optional(unit.get("period")),
        })

    for topic in proposals:
        if not isinstance(topic, dict):
            raise ValueError("Sujet invalide.")

        tid = _required(topic.get("id"), "topic.id")

        if tid in topic_ids:
            raise ValueError(f"Sujet dupliqué : {tid}")

        topic_ids.add(tid)

        references = topic.get("unit_ids")

        if not isinstance(references, list) or not references:
            raise ValueError(
                f"Sujet {tid} sans informations."
            )

        if len(references) != len(set(references)):
            raise ValueError(
                f"Associations dupliquées : {tid}"
            )

        missing = set(references) - unit_ids

        if missing:
            raise ValueError(
                f"Sujet {tid} : unités inconnues "
                + ", ".join(sorted(missing)[:10])
            )

        topic_rows.append({
            "TOPIC_ID": tid,
            "TITLE": _required(
                topic.get("title"), f"{tid}.title"
            ),
            "ANGLE": _optional(topic.get("angle")),
            "EDITORIAL_RATIONALE": _optional(
                topic.get("editorial_rationale")
            ),
            "EVIDENCE_COUNT": len(references),
            "REVIEW_COUNT": sum(
                1
                for uid in references
                if next(
                    u["VERIFICATION_STATUS"]
                    for u in unit_rows
                    if u["UNIT_ID"] == uid
                ) != "VERIFIED"
            ),
        })

        for uid in references:
            link_rows.append({
                "TOPIC_ID": tid,
                "UNIT_ID": uid,
            })

    return unit_rows, topic_rows, link_rows


def _merge_rows(
    client: bigquery.Client,
    table: str,
    rows: list[dict],
    key_columns: list[str],
):
    """Stage rows, then insert only missing records."""

    if not rows:
        return

    staging = (
        f"{BASE}._PDF_LIBRARY_STAGE_"
        f"{uuid.uuid4().hex}"
    )

    try:
        job = client.load_table_from_json(
            rows,
            staging,
            job_config=bigquery.LoadJobConfig(
                autodetect=True,
                write_disposition="WRITE_TRUNCATE",
            ),
        )
        job.result()

        columns = list(rows[0])

        # All imports use ID_DOCUMENT as part of identity.
        match_columns = ["ID_DOCUMENT", *key_columns]

        condition = " AND ".join(
            f"T.{col} = S.{col}"
            for col in match_columns
        )

        insert_columns = [
            *columns,
            "CREATED_AT",
        ]

        insert_values = [
            *(f"S.{col}" for col in columns),
            "CURRENT_TIMESTAMP()",
        ]

        sql = f"""
        MERGE `{table}` T
        USING `{staging}` S
        ON {condition}
        WHEN NOT MATCHED THEN
          INSERT ({", ".join(insert_columns)})
          VALUES ({", ".join(insert_values)})
        """

        _query(client, sql)

    finally:
        client.delete_table(
            staging,
            not_found_ok=True,
        )


def import_document_library(payload: dict) -> dict:
    """Persist an existing PDF Studio V8 export."""

    document_id = _required(
        payload.get("id_document"),
        "id_document",
    )

    unit_rows, topic_rows, link_rows = _normalize(
        payload
    )

    client = get_bigquery_client()

    document = _document(client, document_id)

    source_id = _required(
        payload.get("source_id"), "source_id"
    )

    if source_id != document.ID_SOURCE:
        raise ValueError(
            "La source ne correspond pas au document."
        )

    document_hash = (
        payload.get("document_hash")
        or (payload.get("topics") or {}).get(
            "document_hash"
        )
    )

    if not document_hash:
        raise ValueError(
            "Empreinte SHA-256 du PDF manquante. "
            "Réenregistrer le document avec son PDF "
            "original et fournir document_hash."
        )

    if document_hash.lower() != document.SHA256.lower():
        raise ValueError(
            "Le document_hash ne correspond pas "
            "au PDF enregistré."
        )

    if document.PAGE_COUNT is not None:
        if any(
            row["PDF_PAGE"] > document.PAGE_COUNT
            for row in unit_rows
        ):
            raise ValueError(
                "Une information référence une page "
                "hors du document."
            )

    for rows in (unit_rows, topic_rows, link_rows):
        for row in rows:
            row["ID_DOCUMENT"] = document_id

    _merge_rows(
        client,
        UNIT,
        unit_rows,
        ["UNIT_ID"],
    )

    _merge_rows(
        client,
        TOPIC,
        topic_rows,
        ["TOPIC_ID"],
    )

    _merge_rows(
        client,
        LINK,
        link_rows,
        ["TOPIC_ID", "UNIT_ID"],
    )

    return {
        "status": "IMPORTED",
        "version": "8.0",
        "id_document": document_id,
        "units": len(unit_rows),
        "topics": len(topic_rows),
        "associations": len(link_rows),
    }
