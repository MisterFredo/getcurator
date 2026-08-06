import re
import uuid
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timezone, date
from dateutil.parser import parse
from typing import Optional, Dict, Any, List
from urllib.parse import urljoin

from utils.bigquery_utils import get_bigquery_client
from google.cloud import bigquery
from config import BQ_PROJECT, BQ_DATASET


# ============================================================
# CONFIG
# ============================================================

TABLE = "RATECARD_CONTENT_RAW"

# ============================================================
# SCRAPING CONFIG
# ============================================================

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}

def clean_raw_file(text: str) -> str:

    """
    Nettoie le fichier brut avant parsing.

    Objectif final pour chaque bloc :

    TITLE :
    DATE_SOURCE :
    RAW_TEXT :
    """

    import re

    text = text.replace("\r\n", "\n")

    blocs = re.split(r"\n?\s*TITLE\s*:", text)

    cleaned_blocks = []

    for bloc in blocs[1:]:

        bloc = bloc.strip()

        if not bloc:
            continue

        lines = bloc.split("\n")

        title = lines[0].strip()

        # -----------------------------
        # DATE_SOURCE
        # -----------------------------

        date_match = re.search(
            r"DATE_SOURCE\s*:\s*([^\n]+)",
            bloc
        )

        date_line = ""

        if date_match:
            date_line = f"DATE_SOURCE : {date_match.group(1).strip()}"

        # -----------------------------
        # RAW TEXT (fusion)
        # -----------------------------

        raw_text = bloc

        raw_text = raw_text.replace(title, "", 1)

        raw_text = re.sub(r"DATE_SOURCE\s*:\s*[^\n]+", "", raw_text)

        raw_text = re.sub(r"RAW_TEXT\s*:", "", raw_text)

        # suppression séparateurs
        raw_text = raw_text.replace("________________", "")

        # nettoyage espaces
        raw_text = re.sub(r"\n{3,}", "\n\n", raw_text)

        raw_text = raw_text.strip()

        cleaned_block = f"""TITLE : {title}

{date_line}

RAW_TEXT :
{raw_text}
"""

        cleaned_blocks.append(cleaned_block.strip())

    return "\n\n".join(cleaned_blocks)

# ============================================================
# PARSE DATE (FR → ISO)
# ============================================================

def parse_date(date_str):

    try:
        return parse(date_str, dayfirst=True, fuzzy=True).date()
    except Exception:
        print("[RAW_IMPORT] date ignorée:", date_str)
        return None

def parse_date_fr(date_str: str):

    mois = {
        "janvier": 1,
        "février": 2,
        "mars": 3,
        "avril": 4,
        "mai": 5,
        "juin": 6,
        "juillet": 7,
        "août": 8,
        "septembre": 9,
        "octobre": 10,
        "novembre": 11,
        "décembre": 12,
    }

    try:

        # nettoyage
        date_str = date_str.strip().lower()

        # suppression parasites éventuels
        date_str = re.sub(r"[–\-].*$", "", date_str)
        date_str = date_str.replace("  ", " ")

        parts = date_str.split()

        if len(parts) < 3:
            return None

        jour = int(parts[0])
        mois_num = mois.get(parts[1])
        annee = int(parts[2])

        if not mois_num:
            return None

        return datetime(annee, mois_num, jour).date()

    except Exception:

        print("[RAW_IMPORT] date ignorée:", date_str)

        return None
        
# ============================================================
# PARSE RAW FILE
# ============================================================

def parse_raw_blocks(text: str) -> List[Dict]:

    print("[RAW_IMPORT] Début parsing fichier")

    text = text.replace("\r\n", "\n")

    blocs = re.split(r"\n?\s*TITLE\s*:", text)

    print(f"[RAW_IMPORT] Nombre de blocs détectés : {len(blocs)-1}")

    results = []

    for i, bloc in enumerate(blocs[1:], start=1):

        bloc = bloc.strip()

        try:

            lines = bloc.split("\n")

            if not lines:
                continue

            # --------------------------------
            # TITLE
            # --------------------------------

            title = lines[0].strip()

            # --------------------------------
            # DATE_SOURCE
            # --------------------------------

            date_source = None

            date_match = re.search(
                r"DATE_SOURCE\s*:\s*([^\n]+)",
                bloc
            )

            if date_match:

                date_str = date_match.group(1).strip()

                # 🔥 PRIORITÉ au comportement historique (FR)
                date_source = parse_date_fr(date_str)

                # fallback si format non FR
                if not date_source:
                    try:
                        date_source = parse(date_str, dayfirst=True, fuzzy=True).date()
                    except Exception:
                        pass

                if not date_source:
                    print("[RAW_IMPORT] date non parsée:", date_str)

            # --------------------------------
            # RAW TEXT
            # --------------------------------

            raw_text = bloc

            raw_text = raw_text.replace(title, "", 1)

            raw_text = re.sub(r"DATE_SOURCE\s*:\s*[^\n]+", "", raw_text)

            raw_text = re.sub(r"RAW_TEXT\s*:", "", raw_text)

            raw_text = raw_text.strip()

            if not raw_text:
                print(f"[RAW_IMPORT] Bloc #{i} vide")
                continue

            results.append(
                {
                    "TITLE": title,
                    "DATE_SOURCE": date_source,
                    "RAW_TEXT": raw_text,
                }
            )

        except Exception as e:

            print(f"[RAW_IMPORT] Bloc #{i} erreur : {e}")

    print(f"[RAW_IMPORT] Blocs valides : {len(results)}")

    return results


# ============================================================
# INSERT BIGQUERY
# ============================================================

def insert_raw_rows(
    rows: List[Dict],
    id_source: str,
    import_type: str = "FILE",

    # 🔥 NEW
    id_primary_company: Optional[str] = None,
):

    print("[RAW_IMPORT] Début insertion BigQuery")

    client = get_bigquery_client()

    table_id = f"{BQ_PROJECT}.{BQ_DATASET}.{TABLE}"

    payload = []

    for r in rows:

        payload.append(
            {
                "ID_RAW": str(uuid.uuid4()),

                "CREATED_AT": datetime.utcnow().isoformat(),

                "STATUS": "STORED",

                # 🔥 NEW
                "ID_PRIMARY_COMPANY": r.get(
                    "ID_PRIMARY_COMPANY",
                    id_primary_company
                ),

                "SOURCE_TITLE": r["TITLE"],

                "IMPORT_TYPE": import_type,

                "DATE_SOURCE": (
                    r["DATE_SOURCE"].strftime("%Y-%m-%d")
                    if r.get("DATE_SOURCE")
                    else None
                ),

                "RAW_TEXT": r["RAW_TEXT"],

                "SOURCE_ID": id_source,

                # 🔥 IMPORTANT
                "SOURCE_URL": r.get("SOURCE_URL"),
            }
        )

    print(f"[RAW_IMPORT] Nombre de lignes à insérer : {len(payload)}")

    job_config = bigquery.LoadJobConfig(
        source_format=bigquery.SourceFormat.NEWLINE_DELIMITED_JSON,
        write_disposition="WRITE_APPEND",
    )

    job = client.load_table_from_json(
        payload,
        table_id,
        job_config=job_config,
    )

    job.result()

    print("[RAW_IMPORT] Insertion BigQuery OK")

    return len(payload)


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


# ============================================================
# STORE RAW CONTENT MOVE FROM SERVICE
# ============================================================

def store_raw_content(
    source_id: str,
    source_title: str,
    raw_text: str,
    source_url: Optional[str] = None,
    
    date_source: Optional[date] = None,

    # 🔥 NEW
    id_primary_company: Optional[str] = None,
) -> str:

    if not source_id:
        raise ValueError("source_id obligatoire")

    if not source_title or not source_title.strip():
        raise ValueError("source_title obligatoire")

    if not raw_text or not raw_text.strip():
        raise ValueError("raw_text vide")

    raw_id = str(uuid.uuid4())

    now_iso = datetime.utcnow().isoformat()

    row = [{

        "ID_RAW": raw_id,

        # 🔥 NEW
        "ID_PRIMARY_COMPANY": id_primary_company,

        "SOURCE_ID": source_id,

        "SOURCE_TITLE": source_title.strip(),
        "SOURCE_URL": source_url,

        "RAW_TEXT": raw_text.strip(),

        "DATE_SOURCE": (
            date_source.isoformat()
            if date_source
            else None
        ),

        "STATUS": "STORED",

        "CREATED_AT": now_iso,

        "PROCESSED_AT": None,

        "GENERATED_CONTENT_ID": None,

        "ERROR_MESSAGE": None,
    }]

    client = get_bigquery_client()

    client.load_table_from_json(
        row,
        TABLE_CONTENT_RAW,
        job_config=bigquery.LoadJobConfig(
            write_disposition="WRITE_APPEND"
        ),
    ).result()

    return raw_id

def normalize_llm_list(values):
    output = []

    for v in values or []:
        if not v:
            continue

        parts = re.split(r",|;", v)

        for p in parts:
            clean = p.strip()
            if clean:
                output.append(clean)

    return list(dict.fromkeys(output))

def list_raw_stock(
    status: Optional[str] = None,
    source_id: Optional[str] = None,
    
    import_type: Optional[str] = None,

    # 🔥 NEW
    id_primary_company: Optional[str] = None,

    limit: int = 50,
    offset: int = 0,
):

    conditions = []
    params = {}

    if status:
        conditions.append("r.STATUS = @status")
        params["status"] = status

    if source_id:
        conditions.append("r.SOURCE_ID = @source_id")
        params["source_id"] = source_id

    if import_type:
        conditions.append("r.IMPORT_TYPE = @import_type")
        params["import_type"] = import_type

    # 🔥 NEW
    if id_primary_company:
        conditions.append(
            "r.ID_PRIMARY_COMPANY = @id_primary_company"
        )
        params["id_primary_company"] = id_primary_company

    where_clause = ""

    if conditions:
        where_clause = "WHERE " + " AND ".join(conditions)

    query = f"""
        SELECT
            r.ID_RAW,

            -- 🔥 NEW
            r.ID_PRIMARY_COMPANY,

            c.NAME AS PRIMARY_COMPANY_NAME,

            r.SOURCE_ID,
            s.NAME AS SOURCE_NAME,

            r.SOURCE_TITLE,
            r.SOURCE_URL,
            r.DATE_SOURCE,

            r.STATUS,
            r.ERROR_MESSAGE,

            r.CREATED_AT,
            r.IMPORT_TYPE,

            COUNT(*) OVER() AS TOTAL_COUNT

        FROM `{TABLE_CONTENT_RAW}` r

        LEFT JOIN `{BQ_PROJECT}.{BQ_DATASET}.RATECARD_SOURCE` s
            ON r.SOURCE_ID = s.SOURCE_ID

        -- 🔥 NEW
        LEFT JOIN `{TABLE_COMPANY}` c
            ON r.ID_PRIMARY_COMPANY = c.ID_COMPANY

        {where_clause}

        ORDER BY r.CREATED_AT DESC

        LIMIT @limit
        OFFSET @offset
    """

    params["limit"] = limit
    params["offset"] = offset

    rows = query_bq(query, params)

    total = rows[0]["TOTAL_COUNT"] if rows else 0

    return {
        "rows": [
            {
                "id_raw": r["ID_RAW"],

                # 🔥 NEW
                "id_primary_company": r.get(
                    "ID_PRIMARY_COMPANY"
                ),

                "primary_company_name": r.get(
                    "PRIMARY_COMPANY_NAME"
                ),

                "source_id": r["SOURCE_ID"],

                "source_name": r.get("SOURCE_NAME"),

                "source_title": r["SOURCE_TITLE"],
                "source_url": r.get("SOURCE_URL"),

                "date_source": r.get("DATE_SOURCE"),

                "status": r["STATUS"],

                "error_message": r.get("ERROR_MESSAGE"),

                "created_at": r["CREATED_AT"],

                "import_type": r.get("IMPORT_TYPE"),
            }
            for r in rows
        ],

        "total": total,
    }
def destock_all_raw_contents(batch_size: int = 50):

    total_processed = 0
    total_errors = 0

    while True:

        result = destock_raw_contents(limit=batch_size)

        if result["total_selected"] == 0:
            break

        # 🔐 Sécurité anti-boucle infinie
        if result["processed"] == 0:
            print("Aucun traitement réussi dans ce batch → arrêt de sécurité")
            break

        total_processed += result["processed"]
        total_errors += result["errors"]

        print(
            f"Batch terminé → processed: {result['processed']} | errors: {result['errors']}"
        )

    return {
        "total_processed": total_processed,
        "total_errors": total_errors,
    }


# ============================================================
# DESTOCK RAW CONTENTS MOVE FROM SERVICE
# ============================================================

def destock_raw_contents(
    limit: int = 5,
    specific_id: Optional[str] = None
) -> Dict[str, Any]:

    # ====================================================
    # 1️⃣ SELECT RAW(S)
    # ====================================================

    if specific_id:

        raws = query_bq(
            f"""
            SELECT *
            FROM `{TABLE_CONTENT_RAW}`
            WHERE ID_RAW = @id_raw
            """,
            {"id_raw": specific_id}
        )

    else:

        raws = query_bq(
            f"""
            SELECT *
            FROM `{TABLE_CONTENT_RAW}`
            WHERE STATUS = 'STORED'
            ORDER BY CREATED_AT DESC
            LIMIT {limit}
            """
        )

    processed = 0
    errors = 0

    # ====================================================
    # 2️⃣ PROCESS LOOP
    # ====================================================

    for raw in raws:

        raw_id = raw["ID_RAW"]

        try:

            print("\n==============================")
            print("RAW ID:", raw_id)
            print("SOURCE_ID:", raw.get("SOURCE_ID"))

            # 🔥 NEW
            print(
                "ID_PRIMARY_COMPANY:",
                raw.get("ID_PRIMARY_COMPANY")
            )

            print("RAW LENGTH:", len(raw.get("RAW_TEXT", "") or ""))
            print("------------------------------")

            if raw["STATUS"] not in ["STORED", "ERROR"]:
                raise ValueError("RAW non traitable (status invalide)")

            # ====================================================
            # PASS TO PROCESSING
            # ====================================================

            update_bq(
                TABLE_CONTENT_RAW,
                {
                    "STATUS": "PROCESSING",
                    "ERROR_MESSAGE": None,
                },
                where={"ID_RAW": raw_id}
            )

            # 🔥 NEW
            id_primary_company = raw.get(
                "ID_PRIMARY_COMPANY"
            )

            # ====================================================
            # GENERATE CONTENT
            # ====================================================

            summary = generate_summary(
                source_id=raw.get("SOURCE_ID"),
                source_text=raw.get("RAW_TEXT", "")
            )

            concepts_llm = normalize_llm_list(
                summary.get("concepts", [])
            )

            solutions_llm = normalize_llm_list(
                summary.get("solutions", [])
            )

            topics_llm = normalize_llm_list(
                summary.get("topics", [])
            )

            acteurs_clean = normalize_llm_list(
                summary.get("acteurs_cites", [])
            )

            # ====================================================
            # CLEAN SOURCE_DATE
            # ====================================================

            raw_source_date = raw.get("DATE_SOURCE")

            source_date_clean = None

            if raw_source_date:

                if (
                    isinstance(raw_source_date, date)
                    and not isinstance(raw_source_date, datetime)
                ):

                    source_date_clean = raw_source_date

                elif isinstance(raw_source_date, datetime):

                    source_date_clean = raw_source_date.date()

                elif isinstance(raw_source_date, str):

                    try:

                        source_date_clean = datetime.strptime(
                            raw_source_date.split("T")[0],
                            "%Y-%m-%d"
                        )

                    except Exception:

                        source_date_clean = None

            # ====================================================
            # BUILD CONTENT MODEL
            # ====================================================

            content_payload = ContentCreate(

                # 🔥 NEW
                id_primary_company=id_primary_company,

                title=summary.get("title"),
                id_raw=raw.get("ID_RAW"),

                source_url=raw.get("SOURCE_URL"),

                source_title=raw.get("SOURCE_TITLE"),

                excerpt=summary.get("excerpt"),

                content_body=summary.get("content_body"),

                chiffres=summary.get("chiffres", []),

                acteurs_cites=summary.get("acteurs_cites", []),

                concepts_llm=concepts_llm,

                solutions_llm=solutions_llm,

                topics_llm=topics_llm,

                mecanique_expliquee=summary.get("mecanique_expliquee"),

                enjeu_strategique=summary.get("enjeu_strategique"),

                point_de_friction=summary.get("point_de_friction"),

                signal_analytique=summary.get("signal_analytique"),

                source_id=raw.get("SOURCE_ID"),

                source_date=source_date_clean,

                author=None,
            )

            content_id = create_content(content_payload)

            # ====================================================
            # MARK RAW AS PROCESSED
            # ====================================================

            update_bq(
                TABLE_CONTENT_RAW,
                {
                    "STATUS": "PROCESSED",
                    "PROCESSED_AT": datetime.utcnow(),
                    "GENERATED_CONTENT_ID": content_id,
                    "ERROR_MESSAGE": None,
                },
                where={"ID_RAW": raw_id}
            )

            processed += 1

        except Exception as e:

            print("\n❌ ERROR DURING DESTOCK:", str(e))

            update_bq(
                TABLE_CONTENT_RAW,
                {
                    "STATUS": "ERROR",
                    "ERROR_MESSAGE": str(e),
                },
                where={"ID_RAW": raw_id}
            )

            errors += 1

    return {
        "processed": processed,
        "errors": errors,
        "total_selected": len(raws),
    }

def delete_raw_content(id_raw: str) -> None:

    if not id_raw:
        raise ValueError("id_raw obligatoire")

    query = f"""
        DELETE FROM `{TABLE_CONTENT_RAW}`
        WHERE ID_RAW = @id_raw
    """

    query_bq(
        query,
        {"id_raw": id_raw}
    )

def retry_raw_content(id_raw: str) -> None:

    if not id_raw:
        raise ValueError("id_raw obligatoire")

    # Vérifier que le RAW est bien en ERROR
    check_query = f"""
        SELECT STATUS
        FROM `{TABLE_CONTENT_RAW}`
        WHERE ID_RAW = @id_raw
    """

    rows = query_bq(check_query, {"id_raw": id_raw})

    if not rows:
        raise ValueError("RAW introuvable")

    if rows[0]["STATUS"] != "ERROR":
        raise ValueError("Retry autorisé uniquement pour les ERROR")

    # Reset propre
    update_bq(
        TABLE_CONTENT_RAW,
        {
            "STATUS": "STORED",
            "ERROR_MESSAGE": None,
        },
        where={"ID_RAW": id_raw}
    )

def get_raw_detail(id_raw: str):

    if not id_raw:
        raise ValueError("id_raw obligatoire")

    query = f"""
        SELECT
            r.ID_RAW,

            -- 🔥 NEW
            r.ID_PRIMARY_COMPANY,

            c.NAME AS PRIMARY_COMPANY_NAME,

            r.SOURCE_ID,
            r.SOURCE_TITLE,
            r.SOURCE_URL,

            r.DATE_SOURCE,

            r.RAW_TEXT,

            r.STATUS,
            r.ERROR_MESSAGE,

            r.IMPORT_TYPE,

            r.CREATED_AT

        FROM `{TABLE_CONTENT_RAW}` r

        -- 🔥 NEW
        LEFT JOIN `{TABLE_COMPANY}` c
            ON r.ID_PRIMARY_COMPANY = c.ID_COMPANY

        WHERE r.ID_RAW = @id_raw

        LIMIT 1
    """

    rows = query_bq(query, {"id_raw": id_raw})

    if not rows:
        return None

    r = rows[0]

    return {

        "id_raw": r["ID_RAW"],

        # 🔥 NEW
        "id_primary_company": r.get(
            "ID_PRIMARY_COMPANY"
        ),

        "primary_company_name": r.get(
            "PRIMARY_COMPANY_NAME"
        ),

        "source_id": r["SOURCE_ID"],

        "source_title": r["SOURCE_TITLE"],
        "source_url": r.get("SOURCE_URL"),

        "date_source": r.get("DATE_SOURCE"),

        "raw_text": r.get("RAW_TEXT"),

        "status": r["STATUS"],

        "error_message": r.get("ERROR_MESSAGE"),

        "import_type": r.get("IMPORT_TYPE"),

        "created_at": r["CREATED_AT"],
    }



def update_raw_content(
    id_raw: str,
    date_source: Optional[str],
    source_title: Optional[str],
    source_url: Optional[str] = None,
    raw_text: Optional[str] = None,

    # 🔥 NEW
    id_primary_company: Optional[str] = None,
):

    client = get_bigquery_client()

    table_id = f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_CONTENT_RAW"

    query = f"""
        UPDATE `{table_id}`
        SET
            DATE_SOURCE = @date_source,

            SOURCE_TITLE = @source_title,
            SOURCE_URL = @source_url,

            RAW_TEXT = @raw_text,

            -- 🔥 NEW
            ID_PRIMARY_COMPANY = @id_primary_company

        WHERE ID_RAW = @id_raw
    """

    job_config = bigquery.QueryJobConfig(
        query_parameters=[

            bigquery.ScalarQueryParameter(
                "date_source",
                "DATE",
                date_source
            ),

            bigquery.ScalarQueryParameter(
                "source_title",
                "STRING",
                source_title
            ),

            bigquery.ScalarQueryParameter(
                "source_url",
                "STRING",
                source_url
            ),

            bigquery.ScalarQueryParameter(
                "raw_text",
                "STRING",
                raw_text
            ),

            # 🔥 NEW
            bigquery.ScalarQueryParameter(
                "id_primary_company",
                "STRING",
                id_primary_company
            ),

            bigquery.ScalarQueryParameter(
                "id_raw",
                "STRING",
                id_raw
            ),
        ]
    )

    client.query(
        query,
        job_config=job_config
    ).result()

def get_raw_stats() -> dict:

    query = f"""
        SELECT

            COUNT(*) AS total,

            SUM(
                CASE WHEN STATUS = 'STORED'
                THEN 1 ELSE 0 END
            ) AS total_stored,

            SUM(
                CASE WHEN STATUS = 'PROCESSING'
                THEN 1 ELSE 0 END
            ) AS total_processing,

            SUM(
                CASE WHEN STATUS = 'ERROR'
                THEN 1 ELSE 0 END
            ) AS total_error,

        FROM `{TABLE_CONTENT_RAW}`
    """

    rows = query_bq(query)

    if not rows:
        return {
            "total": 0,
            "total_stored": 0,
            "total_processing": 0,
            "total_error": 0,
        }

    r = rows[0]

    return {

        "total": r.get("total", 0),

        "total_stored": r.get("total_stored", 0),

        "total_processing": r.get("total_processing", 0),

        "total_error": r.get("total_error", 0),

        # 🔥 NEW

    }
# ============================================================
# SUBSTACK MOVE FROM SERVICE
# ============================================================

def raw_url_exists(url: str) -> bool:
    rows = query_bq(
        f"""
        SELECT 1
        FROM `{TABLE_CONTENT_RAW}`
        WHERE SOURCE_URL = @url
        LIMIT 1
        """,
        {"url": url},
    )
    return bool(rows)
