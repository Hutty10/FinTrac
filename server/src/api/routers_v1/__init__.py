from fastapi import APIRouter

from src.api.routers_v1.auth import router as auth_router

router = APIRouter()

router.include_router(auth_router)
