from fastapi import APIRouter
from api.discovery.routes import router as discovery_routes

router = APIRouter()
router.include_router(discovery_routes)
