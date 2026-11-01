
import json
import time

from config import BQ_PROJECT, BQ_DATASET
from utils.bigquery_utils import query_bq
from utils.llm import run_llm_json
from core.numbers.service import parse_chiffres
from core.numbers.backlog_service import build_prompt
from core.numbers.backlog_llm import validate_output

CONTENT_ID = "6e6da96e-9876-4bde-b20c-c7fd98e2c2fb"

MODELS = [
    "gpt-4o",
    "gpt-6-luna",
]

rows = query_bq(
    f"""
    SELECT CHIFFRES
    FROM `{BQ_PROJECT}.{BQ_DATASET}.RATECARD_CONTENT`
    WHERE ID_CONTENT = @id
    """,
    {"id": CONTENT_ID},
)

if not rows:
    raise RuntimeError("Content not found")

numbers = parse_chiffres(rows[0]["CHIFFRES"] or [])

results = []

for index, number in enumerate(numbers):
    prompt = build_prompt(number)

    for model in MODELS:
        started = time.perf_counter()

        raw = run_llm_json(
            prompt=prompt,
            model=model,
            operation="numbers_benchmark",
        )

        duration = round(time.perf_counter() - started, 2)

        try:
            parsed = validate_output(json.loads(raw))
            status = "ok"
            error = None
        except Exception as exc:
            parsed = {}
            status = "error"
            error = str(exc)

        results.append({
            "position": index,
            "label": number["label"],
            "model": model,
            "status": status,
            "decision": parsed.get("decision"),
            "value": parsed.get("value"),
            "unit": parsed.get("unit"),
            "actor": parsed.get("actor"),
            "duration_seconds": duration,
            "error": error,
        })

        print(
            index,
            model,
            status,
            parsed.get("decision"),
            duration,
        )

with open("/tmp/numbers_benchmark.json", "w") as f:
    json.dump(results, f, ensure_ascii=False, indent=2)

print("\nBENCHMARK COMPLETED")
print("Results: /tmp/numbers_benchmark.json")
