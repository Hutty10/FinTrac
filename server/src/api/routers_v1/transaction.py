from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlmodel.ext.asyncio.session import AsyncSession

from src.api.dependencies.session import get_session
from src.api.dependencies.user import get_current_active_user
from src.models.db.user import User
from src.models.schemas.response import ResponseModel
from src.models.schemas.transaction import (
    TransactionCreate,
    TransactionRead,
    TransactionUpdate,
)
from src.service.transaction import transaction_service

router = APIRouter(prefix="/transactions", tags=["Transactions"])


@router.post(
    "/",
    response_model=ResponseModel[TransactionRead],
    status_code=status.HTTP_201_CREATED,
)
async def create_transaction(
    transaction_data: TransactionCreate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_active_user),
) -> ResponseModel[TransactionRead]:
    """Create a new transaction (Income, Expense, Transfer)"""
    return await transaction_service.create_transaction(
        session, current_user.id, transaction_data
    )


@router.get(
    "/",
    response_model=ResponseModel[list[TransactionRead]],
    status_code=status.HTTP_200_OK,
)
async def get_transactions(
    page: int = 1,
    page_size: int = 20,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_active_user),
) -> ResponseModel[list[TransactionRead]]:
    """Get paginated transactions for the current user"""
    return await transaction_service.get_all_transactions(
        session, current_user.id, page, page_size
    )


@router.get(
    "/{transaction_id}",
    response_model=ResponseModel[TransactionRead],
    status_code=status.HTTP_200_OK,
)
async def get_transaction_by_id(
    transaction_id: UUID,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_active_user),
) -> ResponseModel[TransactionRead]:
    """Get a transaction by its ID for the current user"""
    return await transaction_service.get_transaction_by_id(
        session, current_user.id, transaction_id
    )


@router.patch(
    "/{transaction_id}",
    response_model=ResponseModel[TransactionRead],
    status_code=status.HTTP_200_OK,
)
async def update_transaction(
    transaction_id: UUID,
    transaction_data: TransactionUpdate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_active_user),
) -> ResponseModel[TransactionRead]:
    """Update an existing transaction for the current user"""
    return await transaction_service.update_transaction(
        session, current_user.id, transaction_id, transaction_data
    )


@router.delete(
    "/{transaction_id}",
    response_model=ResponseModel[None],
    status_code=status.HTTP_200_OK,
)
async def delete_transaction(
    transaction_id: UUID,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_active_user),
) -> ResponseModel[None]:
    """Delete a transaction for the current user"""
    return await transaction_service.delete_transaction(
        session, current_user.id, transaction_id
    )
