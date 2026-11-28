"""Require a recorded verdict for every existing local audit location."""
import copy
import json

CONTRACT = "monthly-field-coverage-v1"
INSTRUCTIONS = """
Rends exactement un field_verdict pour CHAQUE emplacement de field_checks,
y compris titres, paragraphes, puces, réserves, conclusion, indicateurs et graphique.
Chaque verdict contient location, verdict (SUPPORTED, ISSUE ou NOT_FACTUAL) et reason.
ISSUE exige au moins une anomalie au même emplacement ; toute anomalie locale
exige le verdict ISSUE. NOT_FACTUAL est réservé à layout, à un graphique absent ou à un champ vide.
Un titre ou surtitre neutre conforme au document reçoit SUPPORTED.
Ne t'arrête pas aux défauts les plus saillants : vérifie chaque proposition du champ.
Distingue les mécanismes, les statuts annoncés/effectifs et les impacts conditionnels
sur le destinataire. Ne confonds pas couverture des Digests et date du fait cité.
Les demandes de style ne sont pas des anomalies matérielles.
Ces verdicts imposent une couverture explicite ; ils ne remplacent pas les issues.
""".strip()


def add_contract(payload):
    if "page" not in payload:
        return payload
    result = copy.deepcopy(payload)
    result["field_audit_contract"] = CONTRACT
    result["field_checks"] = list(payload["locations"])
    return result


def extend_schema(schema, payload):
    if payload.get("field_audit_contract") != CONTRACT:
        return schema
    result = copy.deepcopy(schema)
    result["properties"]["field_verdicts"] = {"type": "array", "items": {
        "type": "object", "properties": {
            "location": {"type": "string", "enum": payload["field_checks"]},
            "verdict": {"type": "string", "enum": ["SUPPORTED", "ISSUE", "NOT_FACTUAL"]},
            "reason": {"type": "string"}},
        "required": ["location", "verdict", "reason"], "additionalProperties": False}}
    result["required"] = list(result["required"]) + ["field_verdicts"]
    return result


def serialize(response, request, original):
    if response.status != "completed" or request["payload"].get("field_audit_contract") != CONTRACT:
        return original(response, request)
    try:
        raw = json.loads(response.output_text or "")
        verdicts = raw.pop("field_verdicts")
        expected = set(request["payload"]["field_checks"])
        if not isinstance(verdicts, list) or len(verdicts) != len(expected) or {v["location"] for v in verdicts} != expected:
            raise ValueError("Chaque champ de la page doit recevoir exactement un verdict.")
        issue_locations = {i["location"] for i in raw.get("issues") or []}
        for verdict in verdicts:
            tokens = verdict["location"].split("/")
            field = tokens[3]
            value = request["payload"]["page"][field]
            if len(tokens) == 5:
                value = value[int(tokens[4])]
            if verdict["verdict"] == "NOT_FACTUAL" and field != "layout" and value is not None and value != "":
                raise ValueError("Un champ non vide doit être examiné, pas classé sans fait.")
            if (set(verdict) != {"location", "verdict", "reason"}
                    or verdict["verdict"] not in {"SUPPORTED", "ISSUE", "NOT_FACTUAL"}
                    or not isinstance(verdict["reason"], str) or not verdict["reason"].strip()
                    or ((verdict["verdict"] == "ISSUE") != (verdict["location"] in issue_locations))):
                raise ValueError("Le verdict d’un champ et ses anomalies divergent.")
        class View:
            output_text = json.dumps(raw, ensure_ascii=False)
            def __getattr__(self, name):
                return getattr(response, name)
        result = original(View(), request)
        result["text"] = response.output_text
        result["field_verdicts"] = verdicts
        return result
    except (ValueError, KeyError, TypeError) as exc:
        result = original(response, request)
        result.update(status="validation_failed", review=None, error={"message": str(exc)})
        return result
