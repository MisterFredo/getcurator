from config import (
    BQ_PROJECT,
    BQ_DATASET,
)

from datetime import (
    datetime,
)

from utils.bigquery_utils import (
    query_bq,
    update_bq,
)

from utils.llm import (
    run_llm,
)


# ============================================================
# TABLE
# ============================================================

TABLE_COMPANY = (
    f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_COMPANY"
)


# ============================================================
# CONFIG
# ============================================================

DEFAULT_BATCH_SIZE = 20


# ============================================================
# SYSTEM PROMPT
# ============================================================

COMPANY_DESCRIPTION_SYSTEM_PROMPT = """
You are a corporate research assistant.

Your task is to write stable factual company identity descriptions
that will be used as background context by an AI conversation system.

Use your general knowledge about the company.

Focus on durable corporate identity information.

Do not focus on recent news, temporary strategic initiatives,
short-term financial performance or current market developments.

Do not invent information when you are uncertain.

Return only the final company description.
""".strip()


# ============================================================
# DESCRIPTION PROMPT
# ============================================================

def _build_description_prompt(
    company_name: str,
) -> str:

    return f"""
Write a concise factual corporate identity description
for the following company:

COMPANY
{company_name}

The description should explain, when relevant:

- country of origin and headquarters
- founding and historical background
- main business activities
- major brands, products, services or platforms
- geographic footprint
- general scale of operations

The description must be evergreen and useful for answering
basic factual questions about the identity of the company.

Do not include:

- recent news
- temporary strategic initiatives
- short-term financial results
- opinions
- speculation

Use the following example as the expected style and level of detail:

"Our diverse portfolio of well over 500 beer brands includes global
brands Budweiser, Corona and Stella Artois; multi-country brands
Beck's, Hoegaarden, Leffe and Michelob ULTRA; and local champions
across many markets. Our brewing heritage dates back more than
600 years, spanning continents and generations, with roots in
Leuven, Belgium, St. Louis in the United States, South Africa
and Brazil. Geographically diversified across developed and
developing markets, the group operates internationally with
a large workforce across dozens of countries."

Write one coherent paragraph in English.

Return only the description.
""".strip()


# ============================================================
# GENERATE ONE
# ============================================================

def generate_company_description(
    company_id: str,
):

    rows = query_bq(
        f"""
        SELECT

            ID_COMPANY,

            NAME,

            DESCRIPTION

        FROM `{TABLE_COMPANY}`

        WHERE
            ID_COMPANY = @company_id

        LIMIT 1
        """,
        {
            "company_id": company_id,
        },
    ) or []

    if not rows:

        raise ValueError(
            "Company not found."
        )

    company = rows[0]

    # ========================================================
    # EXISTING DESCRIPTION
    # ========================================================

    existing_description = (
        company.get("DESCRIPTION")
        or ""
    ).strip()

    if existing_description:

        return {
            "company_id": company_id,
            "name": company["NAME"],
            "status": "skipped",
            "reason": "description_exists",
        }

    # ========================================================
    # GENERATE
    # ========================================================

    description = run_llm(
        prompt=_build_description_prompt(
            company["NAME"],
        ),
        temperature=0.1,
        system_prompt=
            COMPANY_DESCRIPTION_SYSTEM_PROMPT,
    ).strip()

    if not description:

        return {
            "company_id": company_id,
            "name": company["NAME"],
            "status": "failed",
            "reason": "empty_llm_response",
        }

    # ========================================================
    # SAVE
    # ========================================================

    update_bq(
        table=TABLE_COMPANY,
        fields={
            "DESCRIPTION": description,
            "UPDATED_AT":
                datetime.utcnow().isoformat(),
        },
        where={
            "ID_COMPANY": company_id,
        },
    )

    return {
        "company_id": company_id,
        "name": company["NAME"],
        "status": "generated",
        "description": description,
    }


# ============================================================
# GENERATE MISSING
# ============================================================

def generate_missing_company_descriptions(
    limit: int = DEFAULT_BATCH_SIZE,
):

    limit = max(
        1,
        min(
            limit,
            100,
        ),
    )

    companies = query_bq(
        f"""
        SELECT

            ID_COMPANY,

            NAME

        FROM `{TABLE_COMPANY}`

        WHERE
            IS_ACTIVE = TRUE

        AND (
            DESCRIPTION IS NULL
            OR TRIM(DESCRIPTION) = ""
        )

        ORDER BY
            UPPER(NAME)

        LIMIT {limit}
        """
    ) or []

    results = []

    for company in companies:

        try:

            result = (
                generate_company_description(
                    company_id=
                        company["ID_COMPANY"],
                )
            )

        except Exception as e:

            result = {
                "company_id":
                    company["ID_COMPANY"],

                "name":
                    company["NAME"],

                "status":
                    "failed",

                "reason":
                    str(e),
            }

        results.append(
            result,
        )

    generated = sum(
        1
        for result in results
        if result["status"] == "generated"
    )

    failed = sum(
        1
        for result in results
        if result["status"] == "failed"
    )

    skipped = sum(
        1
        for result in results
        if result["status"] == "skipped"
    )

    return {
        "requested": len(companies),
        "generated": generated,
        "failed": failed,
        "skipped": skipped,
        "results": results,
    }
