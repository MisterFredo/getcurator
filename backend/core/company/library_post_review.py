"""Append manual decisions independently of automatic qualification."""

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
