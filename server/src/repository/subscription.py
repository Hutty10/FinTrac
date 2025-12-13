from src.models.db.subscription import Subscription
from src.repository.base import BaseRepository


class SubscriptionRepository(BaseRepository[Subscription]):
    def __init__(self):
        super().__init__(Subscription)
