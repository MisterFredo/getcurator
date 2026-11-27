"""Bind Monthly KPIs to frozen evidence, or omit unsupported standalone KPIs."""
from decimal import Decimal
import re
from core.production.digest_source import EVIDENCE_FIELDS
from core.production.evidence_catalog import _chunks


def normalize_monthly_metrics(document, corpus, numbers, normalizations=None):
    sources = {source.id: source for source in document.sources}
    reports = {(report.report_id, report.version_number): report.payload for report in corpus.reports}
    narrative = " ".join([getattr(document, "title", ""), getattr(document, "subtitle", "")] + [
        text for page in document.pages for text in
        [page.title, page.eyebrow, *page.paragraphs, *page.bullets, page.takeaway, *page.cautions]
    ])
    narrative_values = numbers(narrative)
    for page in document.pages:
        retained = []
        has_narrative = any(text.strip() for text in [*page.paragraphs, *page.bullets, page.takeaway])
        for metric in page.metrics:
            source = sources[metric.source_id]
            value = Decimal(str(metric.value))
            if value in numbers(source.quote):
                retained.append(metric)
                continue
            report = reports.get((source.report_id, source.report_version))
            if not report or report.get("source_type") != "DIGEST_SUBJECT":
                retained.append(metric)
                continue
            matches = [(i, content) for i, content in enumerate(report.get("contents") or [])
                       if content.get("content_id") == source.content_id]
            if len(matches) != 1:
                retained.append(metric)
                continue
            index, content = matches[0]
            witnesses = []
            # Structured numbers first; never use a title/profile/other content.
            for field in ("chiffres", *(field for field in EVIDENCE_FIELDS if field != "chiffres")):
                raw = content.get(field)
                values = list(enumerate(raw)) if field == "chiffres" and isinstance(raw, list) else ([] if field == "chiffres" else [(None, raw)])
                for offset, text in values:
                    if not isinstance(text, str):
                        continue
                    for chunk in _chunks(text):
                        if value in numbers(chunk):
                            pointer = f"/contents/{index}/{field}" + (f"/{offset}" if offset is not None else "")
                            witnesses.append((pointer, chunk))
            if witnesses and len(document.sources) < 100:
                pointer, quote = witnesses[0]
                suffix = 1
                new_id = f"{source.id[:28]}-num-{suffix}"
                while new_id in sources:
                    suffix += 1
                    new_id = f"{source.id[:28]}-num-{suffix}"
                evidence = source.model_copy(update={"id": new_id, "json_pointer": pointer, "quote": quote})
                document.sources.append(evidence)
                sources[new_id] = evidence
                metric.source_id = new_id
                page.source_ids = list(dict.fromkeys([*page.source_ids, new_id]))
                retained.append(metric)
                if normalizations is not None:
                    normalizations.append({"kind": "NUMERIC_WITNESS_ATTACHED", "page_id": page.page_id,
                        "metric_label": metric.label, "value": metric.value, "old_source_id": source.id,
                        "source_id": new_id, "content_id": source.content_id, "json_pointer": pointer,
                        "note": "Présence numérique vérifiée ; sens, unité et périmètre restent soumis au contrôle éditorial."})
            elif (not witnesses and value not in narrative_values and has_narrative
                  and not re.search(r"(?<!\d)" + re.escape(format(value.normalize(), "f")).replace(r"\.", r"[.,]") + r"(?!\d)", narrative)):
                if normalizations is not None:
                    normalizations.append({"kind": "UNSUPPORTED_STANDALONE_METRIC_OMITTED", "page_id": page.page_id,
                        "metric_label": metric.label, "value": metric.value, "display_value": metric.display_value,
                        "source_id": source.id, "content_id": source.content_id,
                        "reason": "Valeur non vérifiable dans les champs analytiques avec les formats numériques pris en charge ; aucune occurrence numérique directe repérée dans le texte."})
            else:
                # Do not leave an unsupported claim in prose, guess a binding
                # across contents, or create an empty metrics-only page.
                retained.append(metric)
        page.metrics = retained
        if page.layout == "METRICS" and not retained and has_narrative:
            page.layout = "ANALYSIS"
