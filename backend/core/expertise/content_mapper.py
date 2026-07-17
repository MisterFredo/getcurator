# backend/core/expertise/content_mapper.py

from api.expertise.models import (
    ExpertiseContent,
)


# ============================================================
# FIND PRIMARY LOGO
# ============================================================

def find_primary_logo(
    companies: list[dict],
    primary_company_id: str | None,
) -> str | None:

    if (
        not primary_company_id
        or not companies
    ):
        return None

    for company in companies:

        if (
            company.get("id_company")
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
    row: dict,
) -> ExpertiseContent:

    companies = (
        row.get("companies")
        or []
    )

    primary_logo = find_primary_logo(
        companies=companies,
        primary_company_id=row.get(
            "ID_PRIMARY_COMPANY"
        ),
    )

    return ExpertiseContent(

        id=row.get("id"),

        title=row.get("title"),

        excerpt=row.get("excerpt"),

        published_at=row.get(
            "published_at"
        ),

        url=(
            "https://www.getcurator.ai/feed"
            f"?analysis_id={row.get('id')}"
        ),

        primary_company_logo=primary_logo,

        companies=companies,

        solutions=(
            row.get("solutions")
            or []
        ),

        topics=(
            row.get("topics")
            or []
        ),

        universes=(
            row.get("universes")
            or []
        ),

        concepts=(
            row.get("concepts")
            or []
        ),
    )


# ============================================================
# NORMALIZE CONTENTS
# ============================================================

def normalize_contents(
    rows: list[dict],
) -> list[ExpertiseContent]:

    contents: list[
        ExpertiseContent
    ] = []

    for row in rows:

        try:

            contents.append(
                build_content(row)
            )

        except Exception:

            continue

    return contents
