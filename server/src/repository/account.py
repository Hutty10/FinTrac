from src.models.db.account import Account
from src.repository.base import BaseRepository


class AccountRepository(BaseRepository[Account]):
    """Repository class for account-related operations"""

    def __init__(self):
        super().__init__(Account)
