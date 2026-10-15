from fastapi import APIRouter
from api.production.routes import router as production_routes

router = APIRouter()
router.include_router(production_routes)
