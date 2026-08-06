import re

from datetime import (
    datetime,
    date,
)

from typing import (
    Optional,
    Dict,
    Any,
)

from config import (
    BQ_PROJECT,
    BQ_DATASET,
)

from api.content.models import (
    ContentCreate,
)

from core.content.ai import (
    generate_summary,
)

from core.content.service import (
    create_content,
)

from core.numbers.service import (
    get_numbers_from_content,
)

from core.numbers.backlog_insert_service import (
    insert_backlog_batch,
)

from core.numbers.backlog_llm import (
    process_backlog_row,
)

from core.content.sync_service import (
    after_publish_sync,
)

from utils.bigquery_utils import (
    query_bq,
    update_bq,
)

# ============================================================
# TABLES
# ============================================================

TABLE_CONTENT = f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_CONTENT"
TABLE_CONTENT_RAW = f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_CONTENT_RAW"

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

