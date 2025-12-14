from fastapi import APIRouter

from src.api.routers_v1.auth import router as auth_router
from src.api.routers_v1.transaction import router as transaction_router

router = APIRouter()

router.include_router(auth_router)
router.include_router(transaction_router)
