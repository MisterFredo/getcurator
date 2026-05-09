# backend/api/workspace/__init__.py

from fastapi import APIRouter
from api.workspace.routes import router as workspace_routes

router = APIRouter()
router.include_router(workspace_routes)
