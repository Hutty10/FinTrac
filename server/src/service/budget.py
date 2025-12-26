from uuid import UUID

from src.models.db.budget import Budget
from src.models.schemas.budget import BudgetCreate, BudgetRead, BudgetUpdate
from src.models.schemas.response import ResponseModel
from src.repository.budget import BudgetRepository
from src.service.base import BaseService


class BudgetService(BaseService[Budget, BudgetRepository]):
    def __init__(self):
        super().__init__(BudgetRepository())

    async def create_budget(
        self, session, user_id: UUID, budget_create: BudgetCreate
    ) -> ResponseModel[BudgetRead]:
        budget = Budget.model_validate(budget_create, update={"user_id": user_id})
        created_budget = await self.repository.create(session, budget)
        budget_read = BudgetRead.model_validate(created_budget)
        return ResponseModel[BudgetRead](
            data=budget_read, message="Budget created successfully."
        )

    async def get_budgets_by_user(
        self, session, user_id: UUID, page: int | None, page_size: int | None
    ) -> ResponseModel[list[BudgetRead]]:
        budgets, metadata = await self.repository.get_by_user(
            session, user_id, page, page_size
        )
        budget_reads = [BudgetRead.model_validate(budget) for budget in budgets]
        return ResponseModel[list[BudgetRead]](
            data=budget_reads,
            message="Budgets retrieved successfully.",
            meta=metadata,
        )

    async def get_budget_by_id(
        self, session, budget_id: UUID, user_id: UUID
    ) -> ResponseModel[BudgetRead]:
        budget = await self.repository.get_by_id(session, budget_id)
        if not budget:
            return ResponseModel[BudgetRead](data=None, message="Budget not found.")
        if budget.user_id != user_id:
            return ResponseModel[BudgetRead](data=None, message="Budget not found.")
        budget_read = BudgetRead.model_validate(budget)
        return ResponseModel[BudgetRead](
            data=budget_read, message="Budget retrieved successfully."
        )

    async def update_budget(
        self, session, budget_id: UUID, user_id: UUID, budget_update: BudgetUpdate
    ) -> ResponseModel[BudgetRead]:
        budget = await self.repository.get_by_id(session, budget_id)
        if not budget:
            return ResponseModel[BudgetRead](data=None, message="Budget not found.")
        if budget.user_id != user_id:
            return ResponseModel[BudgetRead](data=None, message="Budget not found.")

        updated_data = budget_update.model_dump(exclude_unset=True)

        updated_budget = await self.repository.update(session, budget_id, updated_data)
        budget_read = BudgetRead.model_validate(updated_budget)
        return ResponseModel[BudgetRead](
            data=budget_read, message="Budget updated successfully."
        )

    async def delete_budget(
        self, session, budget_id: UUID, user_id: UUID
    ) -> ResponseModel[None]:
        budget = await self.repository.get_by_id(session, budget_id)
        if not budget:
            return ResponseModel[None](data=None, message="Budget not found.")
        if budget.user_id != user_id:
            return ResponseModel[None](data=None, message="Budget not found.")

        await self.repository.delete(session, budget_id)
        return ResponseModel[None](data=None, message="Budget deleted successfully.")