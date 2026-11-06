"""Compatibility routes: scan persists discoveries; legacy auto-ingestion is disabled."""
from fastapi import HTTPException
from core.company.watch_discovery_service import active_watch, scan_watch


def collect_url(*args, **kwargs):
    raise HTTPException(409, "Parcours modifié : scanner, sélectionner les URL puis les stocker. Actualiser le frontend.")


def import_text(*args, **kwargs):
    raise HTTPException(409, "L'import direct en Library est suspendu dans le parcours Corpo. Le déstockage sera défini séparément.")
