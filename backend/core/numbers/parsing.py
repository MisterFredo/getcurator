from typing import List, Dict
from config import BQ_PROJECT, BQ_DATASET
from utils.bigquery_utils import query_bq

# ============================================================
# UNIT / SCALE
# ============================================================

def _extract_unit_scale(unit_raw: str):
    u = (unit_raw or "").lower()

    if "%" in u:
        return "PERCENT", None

    if "€" in u or "eur" in u:
        if "billion" in u or "milliard" in u:
            return "EUR", "billion"
        if "million" in u:
            return "EUR", "million"
        if "thousand" in u or "k" in u:
            return "EUR", "thousand"
        return "EUR", None

    return unit_raw.upper() if unit_raw else None, None


# ============================================================
# PARSE CHIFFRES
# ============================================================

def parse_chiffres(chiffres: List[str]) -> List[Dict]:

    results = []

    for line in chiffres:

        if not line or "|" not in line:
            continue

        parts = [p.strip() for p in line.split("|")]

        if len(parts) == 6:
            label, value, unit_raw, actor, market, period = parts
            type_ = None

        elif len(parts) == 7:
            label, value, unit_raw, actor, market, period, type_ = parts

        else:
            continue

        try:
            value = float(value)
        except:
            continue

        unit, scale = _extract_unit_scale(unit_raw)

        results.append({
            "label": label,
            "value": value,
            "unit": unit,
            "scale": scale,
            "actor": actor,
            "zone": market,
            "period": period,
            "type": type_,
        })

    return results


# ============================================================
# RAW NUMBERS
# ============================================================

def get_raw_numbers(limit: int = 200):

    TABLE_CONTENT = f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_CONTENT"

    rows = query_bq(f"""
        SELECT ID_CONTENT, CHIFFRES
        FROM `{TABLE_CONTENT}`
        WHERE CHIFFRES IS NOT NULL
        LIMIT @limit
    """, {"limit": limit})

    results = []

    for r in rows:

        chiffres = r.get("CHIFFRES") or []

        if isinstance(chiffres, str):
            chiffres = chiffres.split("\n")

        for parsed in parse_chiffres(chiffres):
            parsed["id_content"] = r["ID_CONTENT"]
            results.append(parsed)

    return results


# ============================================================
# FROM CONTENT
# ============================================================

def get_numbers_from_content(id_content: str):

    TABLE_CONTENT = f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_CONTENT"

    rows = query_bq(f"""
        SELECT CHIFFRES
        FROM `{TABLE_CONTENT}`
        WHERE ID_CONTENT = @id_content
        LIMIT 1
    """, {"id_content": id_content})

    if not rows:
        return []

    chiffres = rows[0].get("CHIFFRES") or []

    if isinstance(chiffres, str):
        chiffres = chiffres.split("\n")

    return parse_chiffres(chiffres)
