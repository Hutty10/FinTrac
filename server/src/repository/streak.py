from src.models.db.streak import Streak
from src.repository.base import BaseRepository


class StreakRepository(BaseRepository[Streak]):
    def __init__(self):
        super().__init__(Streak)
