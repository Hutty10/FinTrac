from fastapi import APIRouter

from src.api.routers_v1.account import router as account_router
from src.api.routers_v1.auth import router as auth_router
from src.api.routers_v1.budget import router as budget_router
from src.api.routers_v1.transaction import router as transaction_router
from src.api.routers_v1.user import router as user_router

router = APIRouter()

router.include_router(auth_router)
router.include_router(user_router)
router.include_router(transaction_router)
router.include_router(account_router)
router.include_router(budget_router)
