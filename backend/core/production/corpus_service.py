import hashlib
import json

from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from core.production.models import (
    ProductionCorpusCounts,
    ProductionEvidenceReference,
    ProductionPrepareRequest,
    ProductionPreparedCorpus,
    ProductionReportSnapshot,
)

from core.touch.notebook_models import (
    TouchCorpusNotebook,
)

from core.touch.notebook_report_service import (
    get_touch_report,
)


# ============================================================
# JSON AND HASHING
# ============================================================

def _canonical_json(value: Any) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )


def _sha256(value: Any) -> str:
    return hashlib.sha256(
        _canonical_json(value).encode("utf-8")
    ).hexdigest()


# ============================================================
# EVIDENCE INDEX
# ============================================================

EVIDENCE_COLLECTIONS = (
    ("notes", "note_id", "NOTE"),
    ("events", "event_id", "EVENT"),
    ("validated_numbers", "number_id", "NUMBER"),
    ("sections", "section_id", "SECTION"),
    (
        "executive_summary",
        "summary_id",
        "SUMMARY",
    ),
    (
        "cross_readings",
        "reading_id",
        "CROSS_READING",
    ),
)


def _build_evidence_index(
    snapshot: ProductionReportSnapshot,
    notebook: TouchCorpusNotebook,
) -> list[ProductionEvidenceReference]:
    references: list[
        ProductionEvidenceReference
    ] = []

    for collection_name, id_field, kind in (
        EVIDENCE_COLLECTIONS
    ):
        seen_ids: set[str] = set()

        for item in getattr(
            notebook,
            collection_name,
        ):
            local_id = getattr(
                item,
                id_field,
            )

            if not local_id.strip():
                raise ValueError(
                    f"Rapport {snapshot.report_id} : "
                    f"identifiant vide dans "
                    f"{collection_name}."
                )

            if local_id in seen_ids:
                raise ValueError(
                    f"Rapport {snapshot.report_id} : "
                    f"identifiant dupliqué dans "
                    f"{collection_name} : {local_id}."
                )

            seen_ids.add(local_id)

            # JSON tuple encoding avoids collisions even
            # when original identifiers contain separators.
            reference_id = _canonical_json(
                [
                    snapshot.report_id,
                    snapshot.version_number,
                    kind,
                    local_id,
                ]
            )

            references.append(
                ProductionEvidenceReference(
                    reference_id=reference_id,
                    report_id=snapshot.report_id,
                    report_version=(
                        snapshot.version_number
                    ),
                    kind=kind,
                    local_id=local_id,
                )
            )

    return references


# ============================================================
# PREPARE PRODUCTION CORPUS
# ============================================================

def prepare_production_corpus(
    request: ProductionPrepareRequest,
) -> ProductionPreparedCorpus:
    snapshots: list[
        ProductionReportSnapshot
    ] = []

    evidence_index: list[
        ProductionEvidenceReference
    ] = []

    content_ids: set[str] = set()
    number_ids: set[str] = set()

    totals = {
        "notes": 0,
        "events": 0,
        "number_occurrences": 0,
        "sections": 0,
        "executive_summary_items": 0,
        "cross_readings": 0,
    }

    for report_id in request.report_ids:
        report = get_touch_report(
            report_id=report_id,
        )

        if report is None:
            raise ValueError(
                "Rapport Touch introuvable : "
                f"{report_id}."
            )

        if report.get("report_id") != report_id:
            raise ValueError(
                "Identifiant incohérent pour "
                f"le rapport {report_id}."
            )

        version = report.get(
            "version_number"
        )

        if (
            isinstance(version, bool)
            or not isinstance(version, int)
            or version < 1
        ):
            raise ValueError(
                f"Rapport {report_id} : "
                "version absente ou invalide."
            )

        if not isinstance(
            report.get("notebook"),
            dict,
        ):
            raise ValueError(
                f"Rapport {report_id} : "
                "notebook sauvegardé absent."
            )

        notebook = (
            TouchCorpusNotebook.model_validate(
                report["notebook"]
            )
        )

        # Independent JSON copy of the saved response.
        # No article or canonical Numbers reload.
        payload = json.loads(
            _canonical_json(report)
        )

        snapshot = (
            ProductionReportSnapshot(
                report_id=report_id,
                version_number=version,
                snapshot_sha256=_sha256(
                    payload
                ),
                payload=payload,
            )
        )

        snapshots.append(snapshot)

        evidence_index.extend(
            _build_evidence_index(
                snapshot=snapshot,
                notebook=notebook,
            )
        )

        content_ids.update(
            report.get("content_ids")
            or []
        )

        number_ids.update(
            number.number_id
            for number
            in notebook.validated_numbers
        )

        totals["notes"] += len(
            notebook.notes
        )

        totals["events"] += len(
            notebook.events
        )

        totals[
            "number_occurrences"
        ] += len(
            notebook.validated_numbers
        )

        totals["sections"] += len(
            notebook.sections
        )

        totals[
            "executive_summary_items"
        ] += len(
            notebook.executive_summary
        )

        totals["cross_readings"] += len(
            notebook.cross_readings
        )

    # Stable content hash, independent of production_id
    # and preparation time.
    corpus_sha256 = _sha256(
        {
            "request": request.model_dump(
                mode="json",
            ),
            "reports": [
                {
                    "report_id": (
                        snapshot.report_id
                    ),
                    "version_number": (
                        snapshot.version_number
                    ),
                    "snapshot_sha256": (
                        snapshot.snapshot_sha256
                    ),
                }
                for snapshot in snapshots
            ],
        }
    )

    return ProductionPreparedCorpus(
        production_id=str(uuid4()),
        prepared_at=datetime.now(
            timezone.utc,
        ),
        request=request,
        reports=snapshots,
        evidence_index=evidence_index,
        counts=ProductionCorpusCounts(
            reports=len(snapshots),
            unique_contents=len(
                content_ids
            ),
            unique_number_ids=len(
                number_ids
            ),
            **totals,
        ),
        corpus_sha256=corpus_sha256,
    )
