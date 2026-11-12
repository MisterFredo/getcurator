"""Requalify only unresolved automatic employee verdicts."""

import argparse
import json
import logging

from core.company import library_post_funnel as funnel
from core.company.library_post_review import EMPLOYEE_ROLE, TABLE as REVIEW_TABLE
from core.library import company_watch_library as library

logger = logging.getLogger(__name__)


def _candidates(limit):
    limit_sql = "LIMIT @limit" if limit is not None else ""
    params = [library._p("version", "STRING", funnel.VERSION),
              library._p("revision", "STRING", funnel.RULE_REVISION)]
    if limit is not None:
        params.append(library._p("limit", "INT64", limit))
    return library._query(f"""
        WITH latest AS (
            SELECT ID_COMPANY, ID_DOCUMENT, VERDICT, TYPE_PRINCIPAL, MOTIF, RULE_REVISION
            FROM `{funnel.TABLE}` WHERE VERSION=@version
            QUALIFY ROW_NUMBER() OVER (
                PARTITION BY ID_COMPANY, ID_DOCUMENT
                ORDER BY CREATED_AT DESC, RULE_REVISION DESC, VERDICT, TYPE_PRINCIPAL
            )=1
        )
        SELECT d.ID_COMPANY, d.ID_DOCUMENT, d.AUTHOR_NAME, d.TITLE, d.SOURCE_URL,
               c.NAME AS COMPANY_NAME, w.AUTHOR_NAME AS WATCH_AUTHOR,
               d.TEXT_STORAGE_URI, d.METADATA_STORAGE_URI, 'EMPLOYEE' AS SOURCE_ROLE,
               v.TYPE_PRINCIPAL AS OLD_TYPE, v.MOTIF AS OLD_MOTIF
        FROM latest v
        JOIN `{library.DOCUMENT}` d ON d.ID_COMPANY=v.ID_COMPANY AND d.ID_DOCUMENT=v.ID_DOCUMENT
        JOIN `{library.BASE}.RATECARD_COMPANY` c ON c.ID_COMPANY=d.ID_COMPANY
        LEFT JOIN `{library.BASE}.RATECARD_COMPANY_WATCH` w
          ON w.ID_COMPANY=d.ID_COMPANY AND w.ID_COMPANY_WATCH=d.ID_COMPANY_WATCH
        WHERE v.VERDICT='A_VERIFIER' AND v.RULE_REVISION IS DISTINCT FROM @revision
          AND d.DOCUMENT_TYPE='LINKEDIN' AND d.ID_COMPANY_WATCH IS NOT NULL
          AND COALESCE(d.EDITORIAL_STATUS,'ACTIVE')='ACTIVE'
          AND d.TEXT_STORAGE_URI IS NOT NULL AND {EMPLOYEE_ROLE}
          AND NOT EXISTS (
              SELECT 1 FROM `{REVIEW_TABLE}` r
              WHERE r.ID_COMPANY=d.ID_COMPANY AND r.ID_DOCUMENT=d.ID_DOCUMENT
          )
        ORDER BY ROW_NUMBER() OVER (
            PARTITION BY v.TYPE_PRINCIPAL ORDER BY d.PUBLISHED_AT DESC NULLS LAST, d.ID_DOCUMENT
        ), v.TYPE_PRINCIPAL, d.ID_DOCUMENT
        {limit_sql}
    """, params)


def _record(row, decision):
    params = [
        library._p("company", "STRING", row["ID_COMPANY"]),
        library._p("id", "STRING", row["ID_DOCUMENT"]),
        library._p("version", "STRING", funnel.VERSION),
        library._p("revision", "STRING", funnel.RULE_REVISION),
        library._p("verdict", "STRING", decision["verdict"]),
        library._p("type", "STRING", decision["type_principal"]),
        library._p("motif", "STRING", decision["motif"]),
    ]
    result = library._query(f"""
        INSERT INTO `{funnel.TABLE}`
            (ID_COMPANY, ID_DOCUMENT, VERSION, VERDICT, TYPE_PRINCIPAL, MOTIF, CREATED_AT, RULE_REVISION)
        WITH current_verdict AS (
            SELECT VERDICT, RULE_REVISION
            FROM `{funnel.TABLE}`
            WHERE ID_COMPANY=@company AND ID_DOCUMENT=@id AND VERSION=@version
            ORDER BY CREATED_AT DESC, RULE_REVISION DESC, VERDICT, TYPE_PRINCIPAL LIMIT 1
        )
        SELECT @company, @id, @version, @verdict, @type, @motif, CURRENT_TIMESTAMP(), @revision
        FROM current_verdict
        WHERE VERDICT='A_VERIFIER' AND RULE_REVISION IS DISTINCT FROM @revision
          AND NOT EXISTS (
              SELECT 1 FROM `{REVIEW_TABLE}` WHERE ID_COMPANY=@company AND ID_DOCUMENT=@id
          )
          AND EXISTS (
              SELECT 1 FROM `{library.DOCUMENT}` WHERE ID_COMPANY=@company AND ID_DOCUMENT=@id
                  AND COALESCE(EDITORIAL_STATUS,'ACTIVE')='ACTIVE'
          );
        SELECT @@row_count AS WRITTEN;
    """, params)
    return bool(result and result[0]["WRITTEN"] == 1)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    scope = parser.add_mutually_exclusive_group()
    scope.add_argument("--limit", type=int, default=20)
    scope.add_argument("--all", action="store_true")
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    if args.limit < 1:
        parser.error("--limit doit être positif")
    if args.all and not args.apply:
        parser.error("--all nécessite --apply")
    failures = 0
    for row in _candidates(None if args.all else args.limit):
        try:
            if args.apply:
                with library.document_lock("post-verdict-" + row["ID_DOCUMENT"]):
                    decision = funnel._classify_row(row)
                    written = _record(row, decision)
            else:
                decision = funnel._classify_row(row)
                written = False
            print(json.dumps({
                "id_document": row["ID_DOCUMENT"], "societe": row["COMPANY_NAME"],
                "titre": row["TITLE"], "url": row["SOURCE_URL"],
                "ancien_type": row["OLD_TYPE"], "ancien_motif": row["OLD_MOTIF"],
                "nouvelle_proposition": decision, "enregistre": written,
            }, ensure_ascii=False), flush=True)
        except Exception:
            failures += 1
            logger.exception("Requalification impossible pour %s", row["ID_DOCUMENT"])
    return int(bool(failures))
