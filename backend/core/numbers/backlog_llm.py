import json
import re
from typing import Dict, Any

from utils.llm import run_llm
from core.numbers.backlog_service import build_prompt


# ============================================================
# CONFIG
# ============================================================

DEBUG_LLM = False

VALID_DECISIONS = [
    "KEEP",
    "IGNORE",
]

REQUIRED_FIELDS = [
    "decision",
    "label",
    "value",
    "unit",
]


# ============================================================
# SAFE JSON PARSE
# ============================================================

def safe_parse_json(text: str):

    try:
        return json.loads(text)

    except:

        # 🔥 extraction JSON si GPT ajoute du texte
        match = re.search(r"\{.*\}", text, re.DOTALL)

        if match:
            try:
                return json.loads(match.group())
            except:
                pass

    return None


# ============================================================
# VALIDATION
# ============================================================

def validate_output(parsed: dict):

    if not isinstance(parsed, dict):
        raise ValueError("Output is not a dict")

    # ============================================================
    # DECISION
    # ============================================================

    decision = (
        parsed.get("decision", "")
        .upper()
        .strip()
    )

    if decision not in VALID_DECISIONS:
        raise ValueError(f"Invalid decision: {decision}")

    parsed["decision"] = decision

    # ============================================================
    # KEEP VALIDATION
    # ============================================================

    if decision == "KEEP":

        for field in REQUIRED_FIELDS:

            value = parsed.get(field)

            if value in [None, "", "null"]:
                raise ValueError(f"Missing field: {field}")

        # ========================================================
        # VALUE
        # ========================================================

        try:
            parsed["value"] = float(parsed["value"])
        except:
            raise ValueError("Invalid numeric value")

    return parsed


# ============================================================
# PROCESS ROW
# ============================================================

def process_backlog_row(row: Dict[str, Any]) -> Dict[str, Any]:

    prompt = build_prompt(row)

    try:

        response = run_llm(
            prompt=prompt,
            temperature=0
        )

        # ========================================================
        # DEBUG
        # ========================================================

        if DEBUG_LLM:
            print("RAW LLM:", response)

        # ========================================================
        # PARSE
        # ========================================================

        parsed = safe_parse_json(response)

        if not parsed:
            raise ValueError("Invalid JSON from LLM")

        # ========================================================
        # VALIDATION
        # ========================================================

        parsed = validate_output(parsed)

        # ========================================================
        # RESULT
        # ========================================================

        return {
            "status": "ok",
            "input": row,
            "output": parsed,
        }

    except Exception as e:

        return {
            "status": "error",
            "input": row,
            "error": str(e),
        }
