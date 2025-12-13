from src.models.db.transaction import Transaction
from src.repository.base import BaseRepository


class TransactionRepository(BaseRepository[Transaction]):
    def __init__(self):
        super().__init__(Transaction)
