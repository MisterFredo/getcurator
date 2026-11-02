from fastapi import APIRouter
from api.library.routes import router as library_routes

router = APIRouter()
router.include_router(library_routes)
