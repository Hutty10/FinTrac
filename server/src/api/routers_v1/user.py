from fastapi import APIRouter, Depends
from sqlmodel.ext.asyncio.session import AsyncSession

from src.api.dependencies.session import get_session
from src.api.dependencies.user import get_current_active_user
from src.models.db.user import User
from src.models.schemas.response import ResponseModel
from src.models.schemas.user import ChangePassword, UserRead, UserUpdate
from src.service.user import UserService

router = APIRouter(
    prefix="/users",
    tags=["Users"],
)


@router.put("/change-password", response_model=ResponseModel[None])
async def change_password(
    data: ChangePassword,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session),
    service: UserService = Depends(),
) -> ResponseModel[None]:
    """Change password for the current user."""
    return await service.change_password(session=session, user=current_user, data=data)


@router.put("/update", response_model=ResponseModel[UserRead])
async def update_user(
    data: UserUpdate,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session),
    service: UserService = Depends(),
) -> ResponseModel[UserRead]:
    """Update the current user's information."""
    return await service.update_user(session=session, user=current_user, data=data)


@router.get("/me", response_model=ResponseModel[UserRead])
async def get_current_user(
    current_user: User = Depends(get_current_active_user),
    service: UserService = Depends(),
) -> ResponseModel[UserRead]:
    """Retrieve the current user's information."""
    return await service.get_user(user=current_user)

