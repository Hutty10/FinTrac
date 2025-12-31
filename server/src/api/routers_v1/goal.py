from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlmodel.ext.asyncio.session import AsyncSession

from src.api.dependencies.session import get_session
from src.api.dependencies.user import get_current_active_user
from src.models.db.user import User
from src.models.schemas.goal import GoalCreate, GoalRead, GoalUpdate
from src.models.schemas.response import ResponseModel
from src.service.goal import GoalService

router = APIRouter(
    prefix="/goals",
    tags=["Goals"],
)


@router.post(
    "/", response_model=ResponseModel[GoalRead], status_code=status.HTTP_201_CREATED
)
async def create_goal(
    goal_create: GoalCreate,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session),
    service: GoalService = Depends(),
) -> ResponseModel[GoalRead]:
    """Create a new goal for the current user."""
    return await service.create_goal(
        session=session, user_id=current_user.id, goal_create=goal_create
    )


@router.get("/", response_model=ResponseModel[list[GoalRead]])
async def get_goals(
    page: int = 1,
    page_size: int = 50,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session),
    service: GoalService = Depends(),
) -> ResponseModel[list[GoalRead]]:
    """Retrieve goals for the current user with optional pagination."""
    return await service.get_goals_by_user(
        session=session,
        user_id=current_user.id,
        page=page,
        page_size=page_size,
    )


@router.get("/{goal_id}", response_model=ResponseModel[GoalRead])
async def get_goal_by_id(
    goal_id: UUID,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session),
    service: GoalService = Depends(),
) -> ResponseModel[GoalRead]:
    """Retrieve a specific goal by its ID for the current user."""
    return await service.get_goal_by_id(
        session=session, goal_id=goal_id, user_id=current_user.id
    )


@router.put("/{goal_id}", response_model=ResponseModel[GoalRead])
async def update_goal(
    goal_id: UUID,
    goal_update: GoalUpdate,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session),
    service: GoalService = Depends(),
) -> ResponseModel[GoalRead]:
    """Update a specific goal by its ID for the current user."""
    return await service.update_goal(
        session=session,
        goal_id=goal_id,
        user_id=current_user.id,
        goal_update=goal_update,
    )


@router.delete("/{goal_id}", response_model=ResponseModel[None])
async def delete_goal(
    goal_id: UUID,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session),
    service: GoalService = Depends(),
) -> ResponseModel[None]:
    """Delete a specific goal by its ID for the current user."""
    return await service.delete_goal(
        session=session, goal_id=goal_id, user_id=current_user.id
    )
