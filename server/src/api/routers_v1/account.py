from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlmodel.ext.asyncio.session import AsyncSession

from src.api.dependencies.session import get_session
from src.api.dependencies.user import get_current_active_user
from src.models.db.user import User
from src.models.schemas.account import (
    AccountCreate,
    AccountRead,
    AccountUpdate,
)
from src.models.schemas.response import ResponseModel
from src.models.schemas.transaction import TransactionRead
from src.service.account import AccountService

router = APIRouter(prefix="/accounts", tags=["Accounts"])


@router.post(
    "/",
    response_model=ResponseModel[AccountRead],
    status_code=status.HTTP_201_CREATED,
)
async def create_account(
    account_data: AccountCreate,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session),
    service: AccountService = Depends(AccountService),  # type: ignore
) -> ResponseModel[AccountRead]:
    """Create a new account for the current user."""
    account = await service.create_account(
        session=session,
        user_id=current_user.id,
        account_data=account_data,
    )
    return account


@router.get(
    "/{account_id}",
    response_model=ResponseModel[AccountRead],
    status_code=status.HTTP_200_OK,
)
async def get_account_by_id(
    account_id: UUID,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session),
    service: AccountService = Depends(AccountService),  # type: ignore
) -> ResponseModel[AccountRead]:
    """Retrieve an account by its ID for the current user."""
    return await service.get_account_by_id(
        session=session,
        user_id=current_user.id,
        account_id=account_id,
    )


@router.get(
    "/",
    response_model=ResponseModel[list[AccountRead]],
    status_code=status.HTTP_200_OK,
)
async def get_all_accounts(
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session),
    service: AccountService = Depends(AccountService),  # type: ignore
) -> ResponseModel[list[AccountRead]]:
    """Retrieve all accounts for the current user."""
    return await service.get_all_accounts(
        session=session,
        user_id=current_user.id,
    )


@router.get(
    "/{account_id}/transactions",
    response_model=ResponseModel[list[TransactionRead]],
    status_code=status.HTTP_200_OK,
)
async def get_transactions_for_account(
    account_id: UUID,
    page: int = 1,
    page_size: int = 20,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session),
    service: AccountService = Depends(AccountService),  # type: ignore
) -> ResponseModel[list[TransactionRead]]:
    """Retrieve transactions for a specific account of the current user."""
    return await service.get_transactions_for_account(
        session=session,
        account_id=account_id,
        user_id=current_user.id,
        page=page,
        page_size=page_size,
    )


@router.put(
    "/{account_id}",
    response_model=ResponseModel[AccountRead],
    status_code=status.HTTP_200_OK,
)
async def update_account(
    account_id: UUID,
    account_data: AccountUpdate,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session),
    service: AccountService = Depends(AccountService),  # type: ignore
) -> ResponseModel[AccountRead]:
    """Update an existing account for the current user."""
    return await service.update_account(
        session=session,
        user_id=current_user.id,
        account_id=account_id,
        account_data=account_data,
    )


@router.delete(
    "/{account_id}",
    response_model=ResponseModel[None],
    status_code=status.HTTP_200_OK,
)
async def delete_account(
    account_id: UUID,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session),
    service: AccountService = Depends(AccountService),  # type: ignore
) -> ResponseModel[None]:
    """Delete an account for the current user."""
    return await service.delete_account(
        session=session,
        user_id=current_user.id,
        account_id=account_id,
    )
