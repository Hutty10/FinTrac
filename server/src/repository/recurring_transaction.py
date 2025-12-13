from src.models.db.recurring_transaction import RecurringTransaction
from src.repository.base import BaseRepository


class RecurringTransactionRepository(BaseRepository[RecurringTransaction]):
    def __init__(self):
        super().__init__(RecurringTransaction)
