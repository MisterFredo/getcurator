from fastapi import APIRouter
from api.expertise.routes import router as expertise_routes

router = APIRouter()
router.include_router(expertise_routes)
