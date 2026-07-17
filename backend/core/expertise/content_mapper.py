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
