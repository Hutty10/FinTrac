from uuid import UUID

from sqlmodel.ext.asyncio.session import AsyncSession

from src.core.utils.exceptions.base import BaseAppException
from src.models.db.goal import Goal
from src.models.schemas.goal import GoalCreate, GoalRead, GoalUpdate
from src.models.schemas.response import ResponseModel
from src.repository.currency import CurrencyRepository
from src.repository.goal import GoalRepository
from src.repository.user_pref import UserPrefRepository
from src.service.base import BaseService


class GoalService(BaseService[Goal, GoalRepository]):
    def __init__(self):
        self.currency_repository = CurrencyRepository()
        self.user_pref_repository = UserPrefRepository()
        super().__init__(GoalRepository())

    async def create_goal(
        self, session: AsyncSession, user_id: UUID, goal_create: GoalCreate
    ) -> ResponseModel[GoalRead]:
        """Create a new goal for a user."""
        currency = None
        currency_code = goal_create.currency_code

        if goal_create.currency_code:
            currency = await self.currency_repository.get_by_code(
                session, goal_create.currency_code
            )
            if not currency:
                raise BaseAppException(message="Currency not found.", status_code=404)
            currency_id = currency.id
        else:
            user_pref = await self.user_pref_repository.get_by_user_id(session, user_id)
            if not user_pref:
                raise BaseAppException(
                    message="User preferences not found.", status_code=404
                )
            currency_id = user_pref.default_currency_id
            currency = await self.currency_repository.get_by_id(session, currency_id)
            if currency:
                currency_code = currency.code

        goal = Goal.model_validate(
            goal_create, update={"user_id": user_id, "currency_id": currency_id}
        )
        goal = await self.repository.create(session, goal)

        goal_read = GoalRead.model_validate(
            {
                **goal.model_dump(),
                "currency_code": currency_code,
            }
        )
        return ResponseModel[GoalRead](
            data=goal_read, message="Goal created successfully."
        )

    async def get_goals_by_user(
        self,
        session: AsyncSession,
        user_id: UUID,
        page: int | None,
        page_size: int | None,
    ) -> ResponseModel[list[GoalRead]]:
        """Retrieve goals for a specific user with pagination."""
        goals, metadata = await self.repository.get_by_user(
            session, user_id, page, page_size
        )
        goal_reads = []
        for goal in goals:
            goal_read = GoalRead.model_validate(
                {
                    **goal.model_dump(),
                    "currency_code": goal.currency.code if goal.currency else None,
                }
            )
            goal_reads.append(goal_read)

        return ResponseModel[list[GoalRead]](
            data=goal_reads,
            message="Goals retrieved successfully.",
            meta=metadata,
        )

    async def get_goal_by_id(
        self, session: AsyncSession, goal_id: UUID, user_id: UUID
    ) -> ResponseModel[GoalRead]:
        """Retrieve a specific goal by its ID for a user."""
        goal = await self.repository.get_by_id(session, goal_id)
        if not goal:
            raise BaseAppException(message="Goal not found.", status_code=404)

        if goal.user_id != user_id:
            raise BaseAppException(
                message="Not authorized to access this goal.", status_code=403
            )

        goal_read = GoalRead.model_validate(
            {
                **goal.model_dump(),
                "currency_code": goal.currency.code if goal.currency else None,
            }
        )
        return ResponseModel[GoalRead](
            data=goal_read, message="Goal retrieved successfully."
        )

    async def update_goal(
        self,
        session: AsyncSession,
        goal_id: UUID,
        user_id: UUID,
        goal_update: GoalUpdate,
    ) -> ResponseModel[GoalRead]:
        """Update an existing goal for a user."""
        goal = await self.repository.get_by_id(session, goal_id)
        if not goal:
            raise BaseAppException(message="Goal not found.", status_code=404)

        if goal.user_id != user_id:
            raise BaseAppException(
                message="Not authorized to update this goal.", status_code=403
            )

        updated_data = goal_update.model_dump(exclude_unset=True)
        updated_goal = await self.repository.update(session, goal_id, updated_data)

        goal_read = GoalRead.model_validate(
            {
                **updated_goal.model_dump(),  # type: ignore
                "currency_code": updated_goal.currency.code # type: ignore
                if updated_goal.currency # type: ignore
                else None,
            }
        )
        return ResponseModel[GoalRead](
            data=goal_read, message="Goal updated successfully."
        )

    async def delete_goal(
        self, session: AsyncSession, goal_id: UUID, user_id: UUID
    ) -> ResponseModel[None]:
        """Delete a goal for a user."""
        goal = await self.repository.get_by_id(session, goal_id)
        if not goal:
            raise BaseAppException(message="Goal not found.", status_code=404)
        if goal.user_id != user_id:
            raise BaseAppException(message="Goal not found.", status_code=404)

        await self.repository.delete(session, goal_id)
        return ResponseModel(data=None, message="Goal deleted successfully.")
