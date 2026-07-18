# backend/core/expertise/content_mapper.py

import os

from api.expertise.models import (
    ExpertiseContent,
)

CURATOR_BASE_URL = (
    os.getenv(
        "CURATOR_BASE_URL",
        "https://www.getcurator.ai",
    )
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

        # ====================================================
        # IDENTIFICATION
        # ====================================================

        id=row.get("id"),

        # ====================================================
        # SOURCE
        # ====================================================

        source_id=(
            row.get("source_id")
            or ""
        ),

        source_title=(
            row.get("source_title")
            or ""
        ),

        source_url=(
            row.get("source_url")
            or ""
        ),

        published_at=row.get(
            "published_at"
        ),

        # ====================================================
        # DISPLAY
        # ====================================================

        title=(
            row.get("title")
            or ""
        ),

        excerpt=(
            row.get("excerpt")
            or ""
        ),

        url=(
            f"{CURATOR_BASE_URL}/feed"
            f"?analysis_id={row.get('id')}"
        ),

        primary_company_logo=primary_logo,

        # ====================================================
        # CONTENT
        # ====================================================

        content_body=(
            row.get("content_body")
            or ""
        ),

        signal=(
            row.get("signal_analytique")
            or ""
        ),

        mecanique=(
            row.get("mecanique_expliquee")
            or ""
        ),

        enjeu=(
            row.get("enjeu_strategique")
            or ""
        ),

        friction=(
            row.get("point_de_friction")
            or ""
        ),

        chiffres=(
            row.get("chiffres")
            or ""
        ),

        # ====================================================
        # STRUCTURED DATA
        # ====================================================

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
