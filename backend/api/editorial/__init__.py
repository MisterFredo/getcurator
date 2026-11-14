from fastapi import APIRouter
from api.editorial.routes import router as editorial_routes

router = APIRouter()
router.include_router(editorial_routes)
