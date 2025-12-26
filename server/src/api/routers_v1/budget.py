from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlmodel.ext.asyncio.session import AsyncSession

from src.api.dependencies.session import get_session
from src.api.dependencies.user import get_current_active_user
from src.models.db.user import User
from src.models.schemas.budget import BudgetCreate, BudgetRead, BudgetUpdate
from src.models.schemas.response import ResponseModel
from src.service.budget import BudgetService

router = APIRouter(
    prefix="/budgets",
    tags=["Budgets"],
)


@router.post(
    "/", response_model=ResponseModel[BudgetRead], status_code=status.HTTP_201_CREATED
)
async def create_budget(
    budget_create: BudgetCreate,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session),
    service: BudgetService = Depends(),
) -> ResponseModel[BudgetRead]:
    """Create a new budget for the current user."""
    return await service.create_budget(
        session=session, user_id=current_user.id, budget_create=budget_create
    )


@router.get("/", response_model=ResponseModel[list[BudgetRead]])
async def get_budgets(
    page: int = 1,
    page_size: int = 50,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session),
    service: BudgetService = Depends(),
) -> ResponseModel[list[BudgetRead]]:
    """Retrieve budgets for the current user with optional pagination."""
    return await service.get_budgets_by_user(
        session=session,
        user_id=current_user.id,
        page=page,
        page_size=page_size,
    )


@router.get("/{budget_id}", response_model=ResponseModel[BudgetRead])
async def get_budget_by_id(
    budget_id: UUID,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session),
    service: BudgetService = Depends(),
) -> ResponseModel[BudgetRead]:
    """Retrieve a specific budget by its ID for the current user."""
    return await service.get_budget_by_id(
        session=session,
        budget_id=budget_id,
        user_id=current_user.id,
    )


@router.put("/{budget_id}", response_model=ResponseModel[BudgetRead])
async def update_budget(
    budget_id: UUID,
    budget_update: BudgetUpdate,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session),
    service: BudgetService = Depends(),
) -> ResponseModel[BudgetRead]:
    """Update a specific budget by its ID for the current user."""
    return await service.update_budget(
        session=session,
        budget_id=budget_id,
        user_id=current_user.id,
        budget_update=budget_update,
    )


@router.delete("/{budget_id}", response_model=ResponseModel[None])
async def delete_budget(
    budget_id: UUID,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session),
    service: BudgetService = Depends(),
) -> ResponseModel[None]:
    """Delete a specific budget by its ID for the current user."""
    return await service.delete_budget(
        session=session,
        budget_id=budget_id,
        user_id=current_user.id,
    )
