import re
import uuid
import requests
from datetime import datetime, timezone, date
from typing import Optional, Dict, Any, List


from utils.bigquery_utils import get_bigquery_client
from google.cloud import bigquery
from config import BQ_PROJECT, BQ_DATASET


# ============================================================
# CONFIG
# ============================================================

TABLE = "RATECARD_CONTENT_RAW"

# ============================================================
# MAIN SERVICE
# ============================================================

def import_raw_content(
    text: str,
    id_source: str,
    id_primary_company: Optional[str] = None,
):

    # 1️⃣ nettoyage
    text = clean_raw_file(text)

    # 2️⃣ parsing
    rows = parse_raw_blocks(text)

    # 3️⃣ insertion BQ
    inserted = insert_raw_rows(
        rows,
        id_source,
        id_primary_company=id_primary_company,
    )

    return inserted


def clean_urls(urls_text: str) -> List[str]:

    urls = list(
        {u.strip() for u in urls_text.split("\n") if u.strip()}
    )

    return urls

def url_already_exists(url: str) -> bool:

    client = get_bigquery_client()

    query = f"""
        SELECT 1
        FROM `{BQ_PROJECT}.{BQ_DATASET}.{TABLE}`
        WHERE SOURCE_URL = @url
        LIMIT 1
    """

    from google.cloud import bigquery

    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("url", "STRING", url)
        ]
    )

    rows = list(client.query(query, job_config=job_config))

    return len(rows) > 0

def parse_article_from_url(url: str) -> Dict[str, Any]:

    resp = requests.get(url, headers=HEADERS, timeout=15)
    resp.raise_for_status()

    soup = BeautifulSoup(resp.text, "html.parser")

    # --------------------------------------------------
    # TITLE (robuste mais sans fallback artificiel)
    # --------------------------------------------------
    title = None

    if soup.title:
        title = soup.title.get_text(strip=True)

    # 👉 on garde le comportement historique :
    # si pas de titre exploitable → on rejette
    if not title:
        raise Exception("TITLE vide")

    # --------------------------------------------------
    # DATE (ajout minimal sans casser le reste)
    # --------------------------------------------------
    date_source = None

    # 1️⃣ meta (historique)
    meta_date = soup.find("meta", {"property": "article:published_time"})
    if meta_date and meta_date.get("content"):
        try:
            date_source = parse(meta_date["content"]).date()
        except Exception:
            pass

    # 2️⃣ fallback <time> (ajout contrôlé)
    if not date_source:
        time_tag = soup.find("time")
        if time_tag:
            try:
                date_source = parse(time_tag.get_text(), dayfirst=True, fuzzy=True).date()
            except Exception:
                pass

    # --------------------------------------------------
    # RAW TEXT (STRICTEMENT logique d’avant)
    # --------------------------------------------------
    paragraphs = soup.find_all("p")

    raw_text = "\n".join(
        p.get_text(strip=True)
        for p in paragraphs
        if p.get_text(strip=True)
    ).strip()

    # 👉 comportement historique : on rejette si vide
    if not raw_text:
        raise Exception("RAW_TEXT vide")

    # --------------------------------------------------
    # RETURN
    # --------------------------------------------------
    return {
        "TITLE": title,
        "DATE_SOURCE": date_source,
        "RAW_TEXT": raw_text,
        "SOURCE_URL": url
    }

def import_urls_batch(
    urls_text: str,
    id_source: str,
    id_primary_company: Optional[str] = None,
):

    import time
    import random

    urls = clean_urls(urls_text)

    inserted_rows = []

    imported_count = 0
    skipped_count = 0
    error_count = 0

    print(f"[RAW_IMPORT_URL] URLs reçues : {len(urls)}")

    for i, url in enumerate(urls, start=1):

        try:

            print(f"[RAW_IMPORT_URL] ({i}/{len(urls)}) {url}")

            # --------------------------------------------------
            # SKIP si déjà existant
            # --------------------------------------------------

            if url_already_exists(url):

                skipped_count += 1
                continue

            # --------------------------------------------------
            # PARSE
            # --------------------------------------------------

            parsed = parse_article_from_url(url)

            title = parsed.get("TITLE")

            date_source = parsed.get("DATE_SOURCE")

            raw_text = parsed.get("RAW_TEXT", "")

            if not raw_text.strip():
                raise Exception("RAW_TEXT vide après parsing")

            # --------------------------------------------------
            # Prépare insertion BQ
            # --------------------------------------------------

            inserted_rows.append(
                {
                    "TITLE": title,
                    "DATE_SOURCE": date_source,
                    "RAW_TEXT": raw_text,
                    "SOURCE_URL": parsed.get("SOURCE_URL"),

                }
            )

            imported_count += 1

            # --------------------------------------------------
            # Délai sécurisé (anti-bot)
            # --------------------------------------------------

            time.sleep(random.uniform(7, 12))

        except Exception as e:

            print("[RAW_IMPORT_URL] erreur:", e)

            error_count += 1

    # ----------------------------------------------------------
    # INSERTION GROUPÉE
    # ----------------------------------------------------------

    if inserted_rows:

        insert_raw_rows(
            inserted_rows,
            id_source=id_source,
            import_type="URL",

            # 🔥 NEW
            id_primary_company=id_primary_company,
        )

    # ----------------------------------------------------------
    # MESSAGE SIMPLE POUR FRONT
    # ----------------------------------------------------------

    message_parts = []

    if imported_count:
        message_parts.append(f"{imported_count} importée(s)")

    if skipped_count:
        message_parts.append(f"{skipped_count} déjà existante(s)")

    if error_count:
        message_parts.append(f"{error_count} erreur(s)")

    message = (
        " / ".join(message_parts)
        if message_parts
        else "Aucune URL traitée"
    )

    return {
        "status": "ok",
        "total": len(urls),
        "inserted": imported_count,
        "skipped": skipped_count,
        "errors": error_count,
        "message": message,
    }

def import_urls_csv(
    csv_text: str,
    id_source: str,
):

    import csv
    import io
    import time
    import random

    reader = csv.DictReader(
        io.StringIO(csv_text)
    )

    rows = list(reader)

    inserted_rows = []

    imported_count = 0
    skipped_count = 0
    error_count = 0

    print(
        f"[RAW_IMPORT_CSV] lignes reçues : {len(rows)}"
    )

    for i, row in enumerate(rows, start=1):

        try:

            url = (
                row.get("URL", "")
                .strip()
            )

            id_primary_company = (
                row.get(
                    "ID_PRIMARY_COMPANY",
                    ""
                ).strip()
                or None
            )

            if not url:
                continue

            print(
                f"[RAW_IMPORT_CSV] ({i}/{len(rows)}) {url}"
            )

            # --------------------------------------------------
            # SKIP SI DÉJÀ EXISTANT
            # --------------------------------------------------

            if url_already_exists(url):

                skipped_count += 1
                continue

            # --------------------------------------------------
            # PARSE
            # --------------------------------------------------

            parsed = parse_article_from_url(
                url
            )

            title = parsed.get(
                "TITLE"
            )

            date_source = parsed.get(
                "DATE_SOURCE"
            )

            raw_text = parsed.get(
                "RAW_TEXT",
                ""
            )

            if not raw_text.strip():
                raise Exception(
                    "RAW_TEXT vide après parsing"
                )

            # --------------------------------------------------
            # PRÉPARE INSERTION BQ
            # --------------------------------------------------

            inserted_rows.append(
                {
                    "TITLE": title,

                    "DATE_SOURCE":
                        date_source,

                    "RAW_TEXT":
                        raw_text,

                    "SOURCE_URL":
                        parsed.get(
                            "SOURCE_URL"
                        ),

                    # 🔥 CSV
                    "ID_PRIMARY_COMPANY":
                        id_primary_company,
                }
            )

            imported_count += 1

            # --------------------------------------------------
            # DÉLAI SÉCURISÉ
            # --------------------------------------------------

            time.sleep(
                random.uniform(7, 12)
            )

        except Exception as e:

            print(
                "[RAW_IMPORT_CSV] erreur:",
                e
            )

            error_count += 1

    # ----------------------------------------------------------
    # INSERTION GROUPÉE
    # ----------------------------------------------------------

    if inserted_rows:

        insert_raw_rows(
            inserted_rows,
            id_source=id_source,
            import_type="URL",
        )

    # ----------------------------------------------------------
    # MESSAGE SIMPLE POUR FRONT
    # ----------------------------------------------------------

    message_parts = []

    if imported_count:
        message_parts.append(
            f"{imported_count} importée(s)"
        )

    if skipped_count:
        message_parts.append(
            f"{skipped_count} déjà existante(s)"
        )

    if error_count:
        message_parts.append(
            f"{error_count} erreur(s)"
        )

    message = (
        " / ".join(message_parts)
        if message_parts
        else "Aucune URL traitée"
    )

    return {
        "status": "ok",
        "total": len(rows),
        "inserted": imported_count,
        "skipped": skipped_count,
        "errors": error_count,
        "message": message,
    }


