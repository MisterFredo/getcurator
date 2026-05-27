from fastapi import APIRouter
from api.digest.routes import router as digest_routes

router = APIRouter()
router.include_router(digest_routes)
