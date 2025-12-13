from src.models.db.goal import Goal
from src.repository.base import BaseRepository


class GoalRepository(BaseRepository[Goal]):
    def __init__(self):
        super().__init__(Goal)
