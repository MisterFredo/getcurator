"""Explicit metric verdicts; legacy responses retain their original contract."""
import copy
import json

CONTRACT = "monthly-metric-verdict-v1"
INSTRUCTIONS = """
Pour chaque entrée de metric_checks, rends un verdict distinct dans metric_verdicts.
SUPPORTED signifie que le chiffre, sa signification et le périmètre revendiqué
sont établis par les preuves citées ; un contexte inconnu doit rester inconnu.
N'exige pas une géographie ou une méthodologie pour tout chiffre : vérifie si
leur absence rend son usage précis sur cette page trompeur ou non interprétable.
Si le KPI doit être retiré ou corrigé, verdict ISSUE et anomalie NUMBER à son
emplacement exact. Examine tous les KPI même si le texte comporte déjà des défauts.
N'ajoute pas un seuil ou une règle différente au fil des corrections.
""".strip()


def add_contract(payload):
    page = payload.get("page") or {}
    if not page.get("metrics"):
        return payload
    result = copy.deepcopy(payload)
    # Locations are canonical, authored by audit_requests, never inferred from ID.
    paths = [p for p in payload["locations"] if "/metrics/" in p]
    if len(paths) != len(page["metrics"]):
        raise ValueError("Les emplacements des métriques sont incomplets.")
    result["metric_audit_contract"] = CONTRACT
    result["metric_checks"] = [{"location": path, "metric": metric}
                               for path, metric in zip(paths, page["metrics"])]
    return result


def extend_schema(schema, payload):
    if payload.get("metric_audit_contract") != CONTRACT:
        return schema
    schema = copy.deepcopy(schema)
    schema["properties"]["metric_verdicts"] = {
        "type": "array", "items": {"type": "object", "properties": {
            "location": {"type": "string", "enum": [c["location"] for c in payload["metric_checks"]]},
            "verdict": {"type": "string", "enum": ["SUPPORTED", "ISSUE"]},
            "reason": {"type": "string"}},
            "required": ["location", "verdict", "reason"], "additionalProperties": False}}
    schema["required"] = list(schema["required"]) + ["metric_verdicts"]
    return schema


def serialize(response, request, original):
    payload = request["payload"]
    if response.status != "completed" or payload.get("metric_audit_contract") != CONTRACT:
        return original(response, request)
    try:
        raw = json.loads(response.output_text or "")
        verdicts = raw.pop("metric_verdicts")
        expected = {c["location"] for c in payload["metric_checks"]}
        if not isinstance(verdicts, list) or len(verdicts) != len(expected):
            raise ValueError("Chaque KPI doit recevoir exactement un verdict.")
        if {v["location"] for v in verdicts} != expected:
            raise ValueError("Le contrôle n’a pas couvert chaque KPI exactement une fois.")
        issues = raw.get("issues") or []
        for verdict in verdicts:
            if (set(verdict) != {"location", "verdict", "reason"}
                    or verdict["verdict"] not in {"SUPPORTED", "ISSUE"}
                    or not isinstance(verdict["reason"], str) or not verdict["reason"].strip()):
                raise ValueError("Verdict de métrique invalide.")
            has_issue = any(i.get("location") == verdict["location"] and i.get("code") == "NUMBER" for i in issues)
            if (verdict["verdict"] == "ISSUE") != has_issue:
                raise ValueError("Le verdict du KPI et ses anomalies NUMBER divergent.")
        class View:
            output_text = json.dumps(raw, ensure_ascii=False)
            def __getattr__(self, name):
                return getattr(response, name)
        result = original(View(), request)
        result["text"] = response.output_text
        result["metric_verdicts"] = verdicts
        return result
    except (ValueError, KeyError, TypeError) as exc:
        result = original(response, request)
        result.update(status="validation_failed", review=None, error={"message": str(exc)})
        return result
