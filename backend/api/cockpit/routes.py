from fastapi import (
    APIRouter,
    HTTPException,
)

from core.cockpit.monitoring import (
    get_monitoring,
)

from core.cockpit.operations import (
    publish_all_drafts,
    rebuild_content_company,
    rebuild_content_solution,
    populate_content_enriched,
    matching_full_dismiss,
    backup_prod,
    sync_prod_to_dev,
    continue_all_knowledge,
    restart_destock,
)

from core.cockpit.quality import (
    get_duplicate_titles,
    delete_duplicate_content,
    get_unmatched_companies,
    get_unmatched_solutions,
    get_numbers_structure,
)

from core.company.description_service import (
    generate_missing_company_descriptions,
)

from core.translation.content_translation_service import (
    translate_contents_batch,
)

router = APIRouter()

# ============================================================
# MONITORING
# ============================================================

@router.get("/monitoring")
def monitoring():

    return {
        "status": "ok",
        "monitoring": get_monitoring(),
    }


# ============================================================
# OPERATIONS
# ============================================================

@router.post("/operations/publish-drafts")
def publish_drafts():

    return publish_all_drafts()

@router.post("/operations/translate-missing")
def translate_missing():

    try:

        result = translate_contents_batch(
            target_lang="en",
            fields=[
                "TITLE",
                "EXCERPT",
            ],
            limit=9999,
            only_missing=True,
            content_ids=None,
            source_id=None,
        )

        return {
            "status": "ok",
            "message": (
                "Missing translations completed."
            ),
            "result": result,
        }

    except Exception as e:

        raise HTTPException(
            400,
            f"Erreur batch traduction : {e}",
        )


@router.post("/operations/rebuild-company")
def rebuild_company():

    return rebuild_content_company()


@router.post("/operations/rebuild-solution")
def rebuild_solution():

    return rebuild_content_solution()


@router.post("/operations/populate-content-enriched")
def populate():

    return populate_content_enriched()


@router.post("/operations/matching-dismiss")
def matching_dismiss():

    return matching_full_dismiss()


@router.post("/operations/restart-destock")
def restart():

    return restart_destock()

@router.post(
    "/operations/generate-company-descriptions"
)
def generate_company_descriptions():

    result = (
        generate_missing_company_descriptions(
            limit=100,
        )
    )

    return {
        "status": "ok",
        "message": (
            f'{result["generated"]} company descriptions generated'
            f' · {result["failed"]} failed'
        ),
        "result": result,
    }


@router.post("/operations/backup")
def backup():

    return backup_prod()


@router.post("/operations/sync-dev")
def sync_dev():

    return sync_prod_to_dev()

@router.post(
    "/operations/continue-knowledge"
)
def continue_knowledge():

    return continue_all_knowledge()


# ============================================================
# QUALITY
# ============================================================

@router.get("/quality/duplicate-titles")
def duplicate_titles():

    return {
        "status": "ok",
        "results": get_duplicate_titles(),
    }

@router.delete("/quality/duplicate-titles/{content_id}")
def delete_duplicate_title(
    content_id: str,
):

    return delete_duplicate_content(
        content_id
    )


@router.get("/quality/unmatched-companies")
def unmatched_companies():

    return {
        "status": "ok",
        "results": get_unmatched_companies(),
    }


@router.get("/quality/unmatched-solutions")
def unmatched_solutions():

    return {
        "status": "ok",
        "results": get_unmatched_solutions(),
    }


@router.get("/quality/numbers-structure")
def numbers_structure():

    return {
        "status": "ok",
        "results": get_numbers_structure(),
    }
