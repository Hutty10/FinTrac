from src.models.db.budget import Budget
from src.repository.base import BaseRepository


class BudgetRepository(BaseRepository[Budget]):
    def __init__(self):
        super().__init__(Budget)
