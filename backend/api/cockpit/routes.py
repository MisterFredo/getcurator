from fastapi import APIRouter

from fastapi import APIRouter

from core.cockpit.operations import (
    publish_all_drafts,
    rebuild_content_company,
    rebuild_content_solution,
    populate_content_enriched,
    matching_full_dismiss,
    backup_prod,
    sync_prod_to_dev,
    restart_destock,
)

router = APIRouter()


@router.post("/operations/publish")
def publish():
    return publish_all_drafts()


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
def dismiss():
    return matching_full_dismiss()


@router.post("/operations/backup")
def backup():
    return backup_prod()


@router.post("/operations/sync-dev")
def sync():
    return sync_prod_to_dev()


@router.post("/operations/restart-destock")
def restart():
    return restart_destock()
