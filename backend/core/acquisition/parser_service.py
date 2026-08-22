import re

import requests

from bs4 import BeautifulSoup

from datetime import datetime

from dateutil.parser import parse

from typing import Any, Dict, List

# ============================================================
# SCRAPING CONFIG
# ============================================================

# ============================================================
# SCRAPING CONFIG
# ============================================================

HEADERS = {

    "User-Agent": (
        "Mozilla/5.0 "
        "(Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 "
        "(KHTML, like Gecko) "
        "Chrome/150.0.0.0 Safari/537.36"
    ),

    "Accept": (
        "text/html,"
        "application/xhtml+xml,"
        "application/xml;q=0.9,"
        "image/avif,"
        "image/webp,"
        "*/*;q=0.8"
    ),

    "Accept-Language": (
        "en-GB,en;q=0.9"
    ),

    "Cache-Control": "no-cache",

    "Pragma": "no-cache",

    "Upgrade-Insecure-Requests": "1",

    "Sec-Fetch-Dest": "document",

    "Sec-Fetch-Mode": "navigate",

    "Sec-Fetch-Site": "none",

    "Sec-Fetch-User": "?1",
}

def clean_raw_file(text: str) -> str:

    """
    Nettoie le fichier brut avant parsing.

    Objectif final pour chaque bloc :

    TITLE :
    DATE_SOURCE :
    RAW_TEXT :
    """

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
    

def clean_urls(urls_text: str) -> List[str]:

    urls = list(
        {u.strip() for u in urls_text.split("\n") if u.strip()}
    )

    return urls

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
                        date_source = parse_date(date_str)
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

def parse_article_from_url(
    url: str,
) -> Dict[str, Any]:

    session = requests.Session()

    resp = session.get(
        url,
        headers=HEADERS,
        timeout=20,
        allow_redirects=True,
    )

    print(
        "[PARSER]",
        url,
        "STATUS=",
        resp.status_code,
        "FINAL_URL=",
        resp.url,
        "SIZE=",
        len(resp.text),
    )

    # ========================================================
    # DEBUG 403
    # ========================================================

    if resp.status_code == 403:

        soup_debug = BeautifulSoup(
            resp.text,
            "html.parser",
        )

        paragraphs_debug = (
            soup_debug.find_all(
                "p"
            )
        )

        text_debug = "\n".join(
            p.get_text(
                " ",
                strip=True,
            )
            for p in paragraphs_debug
            if p.get_text(
                " ",
                strip=True,
            )
        )

        print(
            "[PARSER 403]",
            "TITLE=",
            (
                soup_debug.title.get_text(
                    strip=True
                )
                if soup_debug.title
                else None
            ),
        )

        print(
            "[PARSER 403]",
            "PARAGRAPHS=",
            len(
                paragraphs_debug
            ),
            "TEXT_SIZE=",
            len(
                text_debug
            ),
        )

        print(
            "[PARSER 403 PREVIEW]",
            text_debug[:1000],
        )

    # ========================================================
    # HTTP STATUS
    # ========================================================

    resp.raise_for_status()

    # ========================================================
    # HTML
    # ========================================================

    soup = BeautifulSoup(
        resp.text,
        "html.parser",
    )

    # --------------------------------------------------
    # TITLE
    # --------------------------------------------------

    title = None

    if soup.title:

        title = soup.title.get_text(
            strip=True
        )

    if not title:

        raise Exception(
            "TITLE vide"
        )

    # --------------------------------------------------
    # DATE
    # --------------------------------------------------

    date_source = None

    # 1. META

    meta_date = soup.find(
        "meta",
        {
            "property":
                "article:published_time"
        },
    )

    if (
        meta_date
        and meta_date.get(
            "content"
        )
    ):

        try:

            date_source = parse(
                meta_date["content"]
            ).date()

        except Exception:

            pass

    # 2. TIME FALLBACK

    if not date_source:

        time_tag = soup.find(
            "time"
        )

        if time_tag:

            try:

                date_source = parse(
                    time_tag.get_text(),
                    dayfirst=True,
                    fuzzy=True,
                ).date()

            except Exception:

                pass

    # --------------------------------------------------
    # RAW TEXT
    # --------------------------------------------------

    paragraphs = soup.find_all(
        "p"
    )

    raw_text = "\n".join(
        p.get_text(
            strip=True
        )
        for p in paragraphs
        if p.get_text(
            strip=True
        )
    ).strip()

    if not raw_text:

        raise Exception(
            "RAW_TEXT vide"
        )

    # --------------------------------------------------
    # RETURN
    # --------------------------------------------------

    return {
        "TITLE": title,
        "DATE_SOURCE": date_source,
        "RAW_TEXT": raw_text,
        "SOURCE_URL": url,
    }


