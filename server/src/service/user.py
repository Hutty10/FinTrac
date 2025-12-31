from sqlmodel.ext.asyncio.session import AsyncSession

from src.core.utils.exceptions.base import BaseAppException
from src.models.db.user import User
from src.models.schemas.response import ResponseModel
from src.models.schemas.user import ChangePassword, UserRead, UserUpdate
from src.repository.user import UserRepository
from src.service.base import BaseService


class UserService(BaseService[User, UserRepository]):
    def __init__(self):
        super().__init__(UserRepository())

    async def change_password(
        self, session: AsyncSession, user: User, data: ChangePassword
    ) -> ResponseModel[None]:
        if not user.verify_password(data.old_password):
            raise BaseAppException(
                message="Current password not correct", status_code=400
            )
        user.set_password(data.new_password)
        await self.repository.save(session, user)
        return ResponseModel(message="Password successfully changed", data=None)

    async def update_user(
        self, session: AsyncSession, user: User, data: UserUpdate
    ) -> ResponseModel[UserRead]:
        updated_data = data.model_dump(exclude_unset=True)
        updated_user = await self.repository.update(session, user.id, updated_data)
        return ResponseModel(
            message="User successfully updated",
            data=UserRead.model_validate(updated_user),
        )

    async def get_user(self, user: User) -> ResponseModel[UserRead]:
        return ResponseModel(
            message="User succcessfully retrieved", data=UserRead.model_validate(user)
        )
