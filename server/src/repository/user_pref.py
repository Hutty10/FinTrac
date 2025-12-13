from src.models.db.user_pref import UserPreference
from src.repository.base import BaseRepository


class UserPrefRepository(BaseRepository[UserPreference]):
    def __init__(self):
        super().__init__(UserPreference)
