from typing import Dict, List


# ============================================================
# FIND PRIMARY LOGO
# ============================================================

def find_primary_logo(
    companies: List[Dict],
    primary_company_id: str | None,
) -> str | None:

    if (
        not primary_company_id
        or not companies
    ):
        return None

    for company in companies:

        if (
            company.get(
                "id_company"
            )
            == primary_company_id
        ):

            return company.get(
                "media_logo_rectangle_id"
            )

    return None


# ============================================================
# BUILD CONTENT
# ============================================================

def build_content(
    row: Dict,
) -> Dict:

    companies = (
        row.get("companies")
        or []
    )

    primary_logo = (
        find_primary_logo(
            companies=companies,
            primary_company_id=row.get(
                "ID_PRIMARY_COMPANY"
            ),
        )
    )

    return {

        "id":
            row.get("id"),

        "title":
            row.get("title"),

        "excerpt":
            row.get("excerpt"),

        "published_at":
            row.get("published_at"),

        "url":
            (
                "https://www.getcurator.ai/feed"
                f"?analysis_id={row.get('id')}"
            ),

        "primary_company_logo":
            primary_logo,

        "companies":
            companies,

        "solutions":
            row.get("solutions")
            or [],

        "topics":
            row.get("topics")
            or [],

        "universes":
            row.get("universes")
            or [],

        "concepts":
            row.get("concepts")
            or [],
    }
