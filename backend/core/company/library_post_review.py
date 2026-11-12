"""Append manual decisions independently of automatic qualification."""

import json
import uuid

from fastapi import HTTPException

from core.library import company_watch_library as library

TABLE = f"{library.BASE}.RATECARD_LIBRARY_POST_REVIEW"

EMPLOYEE_ROLE = """(d.SOURCE_ROLE='EMPLOYEE' OR w.SOURCE_ROLE='EMPLOYEE'
                    OR w.ID_CONTACT IS NOT NULL)"""

LATEST = f"""SELECT ID_COMPANY, ID_DOCUMENT, ID_REVIEW, VERDICT, TYPE_PRINCIPAL, MOTIF, CREATED_AT
    FROM `{TABLE}`
    QUALIFY ROW_NUMBER() OVER (
        PARTITION BY ID_COMPANY, ID_DOCUMENT ORDER BY CREATED_AT DESC, ID_REVIEW DESC
    )=1"""


def save_review(document_id, verdict, post_type, reason=None):
    from core.company.library_post_funnel import POST_TYPES

    if verdict not in {"SIGNAL_SOCIETE", "PRISE_DE_PAROLE_METIER", "BRUIT", "CORPORATE"}:
        raise ValueError("Verdict de revue invalide")
    if post_type not in POST_TYPES:
        raise ValueError("Type principal invalide")
    reason = (reason or "").strip() or None
    if reason and len(reason) > 1000:
        raise ValueError("Motif limité à 1 000 caractères")

    rows = library._query(f"""
        INSERT INTO `{TABLE}` (ID_REVIEW, ID_COMPANY, ID_DOCUMENT, VERDICT, TYPE_PRINCIPAL, MOTIF, CREATED_AT)
        SELECT @review, d.ID_COMPANY, d.ID_DOCUMENT, @verdict, @type, @reason, CURRENT_TIMESTAMP()
        FROM `{library.DOCUMENT}` d
        LEFT JOIN `{library.BASE}.RATECARD_COMPANY_WATCH` w
            ON w.ID_COMPANY=d.ID_COMPANY AND w.ID_COMPANY_WATCH=d.ID_COMPANY_WATCH
        WHERE d.ID_DOCUMENT=@id AND d.ID_COMPANY_WATCH IS NOT NULL
          AND d.DOCUMENT_TYPE='LINKEDIN'
          AND COALESCE(d.EDITORIAL_STATUS, 'ACTIVE')='ACTIVE'
          AND IF({EMPLOYEE_ROLE}, @verdict!='CORPORATE', @verdict='CORPORATE')
        LIMIT 1;
        SELECT @@row_count AS UPDATED_COUNT;
    """, [
        library._p("review", "STRING", str(uuid.uuid4())),
        library._p("id", "STRING", document_id),
        library._p("verdict", "STRING", verdict),
        library._p("type", "STRING", post_type),
        library._p("reason", "STRING", reason),
    ])
    if not rows or int(rows[0]["UPDATED_COUNT"]) != 1:
        raise HTTPException(409, "Le post n’est plus actif ou le verdict ne correspond pas à son origine")
    return {"status": "ok"}


def _pending_sql():
    from core.company import library_post_funnel as funnel

    return f"""
        SELECT d.ID_COMPANY, d.ID_DOCUMENT, d.TEXT_STORAGE_URI, d.METADATA_STORAGE_URI,
               d.AUTHOR_NAME, w.AUTHOR_NAME AS WATCH_AUTHOR, c.NAME AS COMPANY_NAME,
               v.TYPE_PRINCIPAL, v.MOTIF
        FROM `{library.DOCUMENT}` d
        LEFT JOIN `{library.BASE}.RATECARD_COMPANY_WATCH` w
          ON w.ID_COMPANY=d.ID_COMPANY AND w.ID_COMPANY_WATCH=d.ID_COMPANY_WATCH
        LEFT JOIN `{library.BASE}.RATECARD_COMPANY` c ON c.ID_COMPANY=d.ID_COMPANY
        JOIN (
            SELECT ID_COMPANY, ID_DOCUMENT, VERDICT, TYPE_PRINCIPAL, MOTIF
            FROM `{funnel.TABLE}` WHERE VERSION=@version
            QUALIFY ROW_NUMBER() OVER (
                PARTITION BY ID_COMPANY, ID_DOCUMENT
                ORDER BY CREATED_AT DESC, RULE_REVISION DESC, VERDICT, TYPE_PRINCIPAL
            )=1
        ) v ON v.ID_COMPANY=d.ID_COMPANY AND v.ID_DOCUMENT=d.ID_DOCUMENT
        LEFT JOIN ({LATEST}) r ON r.ID_COMPANY=d.ID_COMPANY AND r.ID_DOCUMENT=d.ID_DOCUMENT
        WHERE d.DOCUMENT_TYPE='LINKEDIN' AND d.ID_COMPANY_WATCH IS NOT NULL
          AND COALESCE(d.EDITORIAL_STATUS,'ACTIVE')='ACTIVE' AND {EMPLOYEE_ROLE}
          AND v.VERDICT='A_VERIFIER' AND r.ID_REVIEW IS NULL
    """


def suggest_review(document_id):
    from core.company import library_post_funnel as funnel

    rows = library._query(
        f"SELECT * FROM ({_pending_sql()}) WHERE ID_DOCUMENT=@id LIMIT 1",
        [library._p("version", "STRING", funnel.VERSION), library._p("id", "STRING", document_id)],
    )
    if not rows:
        raise HTTPException(409, "Ce post ne figure plus dans les publications à vérifier.")
    row = dict(rows[0])
    text = library._read_uri(row["TEXT_STORAGE_URI"])
    context = funnel._context_for_pass(funnel._attribution(row), full_text=True)
    raw = funnel.run_llm_json(
        prompt=json.dumps({
            "societe_suivie": row["COMPANY_NAME"],
            "texte": text[:12000],
            "texte_tronque": len(text) > 12000,
            "motif_initial": row["MOTIF"],
            "type_initial": row["TYPE_PRINCIPAL"],
            **context,
        }, ensure_ascii=False),
        model=funnel.os.getenv("COMPANY_POST_TRIAGE_MODEL") or None,
        temperature=0.0,
        system_prompt=funnel.PROMPT + "\n" + funnel.ATTRIBUTION_PROMPT + """
Pour cette aide à la revue, propose le verdict le mieux étayé parmi
SIGNAL_SOCIETE, PRISE_DE_PAROLE_METIER et BRUIT. Une présence annoncée ou
confirmée à un événement professionnel par le salarié suivi suffit pour
SIGNAL_SOCIETE et EVENEMENT, même sans stand ni prise de parole.
Si aucun signal n'est suffisamment étayé, propose BRUIT et indique
l'information qui manque. N'invente aucun fait ou lien d'attribution.
""",
        profile="smart", operation="company_post_triage",
    )
    try:
        result = json.loads(raw)
    except (TypeError, ValueError) as exc:
        raise HTTPException(502, "Le modèle n’a pas fourni de suggestion exploitable.") from exc
    if (not isinstance(result, dict)
            or result.get("verdict") not in ("SIGNAL_SOCIETE", "PRISE_DE_PAROLE_METIER", "BRUIT")
            or not isinstance(result.get("type_principal"), str)
            or result["type_principal"] not in funnel.POST_TYPES
            or not isinstance(result.get("motif"), str) or not result["motif"].strip()):
        raise HTTPException(502, "Le modèle n’a pas fourni de suggestion exploitable.")
    return {"verdict": result["verdict"], "post_type": result["type_principal"],
            "reason": result["motif"].strip()[:1000]}


def save_reviews(decisions):
    from core.company import library_post_funnel as funnel

    ids = [decision["document_id"] for decision in decisions]
    if not 1 <= len(ids) <= 50 or len(set(ids)) != len(ids):
        raise ValueError("Sélectionnez entre 1 et 50 publications distinctes.")
    for decision in decisions:
        if (decision["verdict"] not in {"SIGNAL_SOCIETE", "PRISE_DE_PAROLE_METIER", "BRUIT"}
                or decision["post_type"] not in funnel.POST_TYPES):
            raise ValueError("Une décision de revue est invalide.")
    rows = library._query(f"""
        INSERT INTO `{TABLE}` (ID_REVIEW, ID_COMPANY, ID_DOCUMENT, VERDICT, TYPE_PRINCIPAL, MOTIF, CREATED_AT)
        SELECT GENERATE_UUID(), pending.ID_COMPANY, pending.ID_DOCUMENT,
               JSON_VALUE(item, '$.verdict'), JSON_VALUE(item, '$.post_type'),
               NULLIF(TRIM(JSON_VALUE(item, '$.reason')), ''), CURRENT_TIMESTAMP()
        FROM UNNEST(JSON_QUERY_ARRAY(@decisions)) item
        JOIN ({_pending_sql()}) pending ON pending.ID_DOCUMENT=JSON_VALUE(item, '$.document_id')
        QUALIFY ROW_NUMBER() OVER (PARTITION BY pending.ID_DOCUMENT ORDER BY pending.ID_COMPANY)=1;
        SELECT @@row_count AS UPDATED_COUNT;
    """, [library._p("version", "STRING", funnel.VERSION),
           library._p("decisions", "STRING", json.dumps(decisions, ensure_ascii=False))])
    updated = int(rows[0]["UPDATED_COUNT"])
    return {"status": "ok", "updated": updated, "skipped": len(ids) - updated}
