"""Manual multi-article newsletter import (Mark Brown format).

Public entry points:
    parse_newsletter(text)
    analyze_newsletter(source_id, text)
    store_newsletter_items(source_id, items)

No new RATECARD_SOURCE rows are created. SOURCE_ID is the newsletter curator.
"""

import hashlib
import re
from datetime import date, datetime
from email.utils import parsedate_to_datetime
from typing import Dict, List, Optional

from config import BQ_PROJECT, BQ_DATASET
from utils.bigquery_utils import query_bq
from core.acquisition.storage_service import insert_raw_rows

SEPARATOR = re.compile(r"(?m)^\s*-{5,}\s*$")
SOURCE_LINE = re.compile(r"^Source\s*:\s*(.+)$", re.IGNORECASE)
DATE_LINE = re.compile(r"^[A-Z][a-z]+\s+\d{1,2},\s+\d{4}$")
URL = re.compile(r"https?://[^\s<>]+", re.IGNORECASE)
HEADER = re.compile(r"^(?:Mark Brown\s*<|Répondre à\s*:|À\s*:|To\s*:|From\s*:|Subject\s*:|Date\s*:|Industry News Update\s*$)", re.IGNORECASE)


def normalize_text(value: str) -> str:
    return (value or "").replace("\r\n", "\n").replace("\r", "\n").replace("\u00a0", " ").strip()


def normalized_hash(value: str) -> str:
    text = normalize_text(value).lower().replace("’", "'").replace("“", '"').replace("”", '"')
    return hashlib.sha256(re.sub(r"\s+", " ", text).strip().encode("utf-8")).hexdigest()


def _lines(text: str) -> List[str]:
    return [line.strip() for line in normalize_text(text).split("\n") if line.strip()]


def _parse_date(value: str) -> Optional[date]:
    try:
        return datetime.strptime(value.strip(), "%B %d, %Y").date()
    except ValueError:
        return None


def _source_label(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def _extract_article_url(source_value: str, body: str) -> Optional[str]:
    """Do not mistake a publication's homepage for an article URL."""
    candidates = URL.findall(body)
    for candidate in candidates:
        candidate = candidate.rstrip(".,);]")
        path = re.sub(r"^https?://[^/]+", "", candidate)
        if path and path != "/":
            return candidate
    return None


def _parse_block(block: str, index: int) -> Optional[Dict]:
    lines = _lines(block)
    if index == 0:
        while lines and HEADER.match(lines[0]):
            lines.pop(0)
    if len(lines) < 4:
        return None
    source_idx = next((i for i, line in enumerate(lines) if SOURCE_LINE.match(line)), None)
    if source_idx is None or source_idx == 0:
        return None
    # Some articles contain a subtitle immediately before Source:.
    title = lines[0]
    subtitle = "\n".join(lines[1:source_idx]).strip()
    source_value = _source_label(SOURCE_LINE.match(lines[source_idx]).group(1))
    date_idx = next((i for i in range(source_idx + 1, min(len(lines), source_idx + 6)) if DATE_LINE.match(lines[i])), None)
    if date_idx is None:
        return None
    publication_date = _parse_date(lines[date_idx])
    if publication_date is None:
        return None
    body = "\n\n".join(lines[date_idx + 1:]).strip()
    if not body:
        return None
    # Keep provenance *in* RAW_TEXT, without creating source records.
    raw_text = f"Original source: {source_value}\nOriginal date: {publication_date.isoformat()}\n\n"
    if subtitle:
        raw_text += subtitle + "\n\n"
    raw_text += body
    return {
        "title": title,
        "original_source": source_value,
        "date_source": publication_date.isoformat(),
        "source_url": _extract_article_url(source_value, body),
        "raw_text": raw_text,
    }


def parse_newsletter(text: str) -> List[Dict]:
    blocks = SEPARATOR.split(normalize_text(text))
    items = []
    for index, block in enumerate(blocks):
        item = _parse_block(block, index)
        if item:
            items.append(item)
    return items


def _existing_hashes(source_id: str) -> set:
    table = f"`{BQ_PROJECT}.{BQ_DATASET}.RATECARD_CONTENT_RAW`"
    rows = query_bq(
        f"SELECT TITLE, RAW_TEXT FROM {table} WHERE SOURCE_ID = @source_id "
        "AND IMPORT_TYPE = 'NEWSLETTER' AND RAW_TEXT IS NOT NULL",
        params={"source_id": source_id},
    )
    return {normalized_hash(f"{row.get('TITLE') or ''}\n{row.get('RAW_TEXT') or ''}") for row in rows}


def _item_hash(item: Dict) -> str:
    return normalized_hash(f"{item.get('title') or ''}\n{item.get('raw_text') or ''}")


def analyze_newsletter(source_id: str, text: str) -> Dict:
    if not source_id:
        raise ValueError("source_id manquant")
    items = parse_newsletter(text)
    existing = _existing_hashes(source_id)
    seen = set()
    result = []
    for item in items:
        digest = _item_hash(item)
        already = digest in existing
        duplicate = digest in seen
        seen.add(digest)
        result.append({**item, "content_hash": digest, "is_existing": already or duplicate,
                       "exists_in_raw": already, "duplicate_in_paste": duplicate,
                       "selected": not (already or duplicate)})
    return {"detected": len(result), "existing": sum(x["is_existing"] for x in result),
            "new": sum(not x["is_existing"] for x in result), "items": result}


def store_newsletter_items(source_id: str, items: List[Dict]) -> Dict:
    if not source_id:
        raise ValueError("source_id manquant")
    existing = _existing_hashes(source_id)
    seen = set()
    rows = []
    skipped = 0
    for item in items:
        if item.get("selected") is False:
            skipped += 1
            continue
        title = (item.get("title") or "").strip()
        raw = (item.get("raw_text") or "").strip()
        if not title or not raw:
            skipped += 1
            continue
        digest = _item_hash(item)
        if digest in existing or digest in seen:
            skipped += 1
            continue
        seen.add(digest)
        date_value = item.get("date_source")
        if isinstance(date_value, str):
            try:
                date_value = date.fromisoformat(date_value)
            except ValueError:
                date_value = None
        rows.append({"TITLE": title, "DATE_SOURCE": date_value,
                     "RAW_TEXT": raw, "SOURCE_URL": item.get("source_url")})
    if rows:
        insert_raw_rows(rows=rows, id_source=source_id, import_type="NEWSLETTER")
    return {"requested": len(items), "stored": len(rows), "skipped": skipped}
