# backend/api/conversation/__init__.py

from fastapi import APIRouter
from api.conversation.routes import router as conversation_routes

router = APIRouter()
router.include_router(conversation_routes)
