from fastapi import APIRouter
from api.acquisition.routes import router as acquisition_routes

router = APIRouter()
router.include_router(acquisition_routes)
