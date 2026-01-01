from src.models.db.security_event import SecurityEvent
from src.repository.base import BaseRepository


class SecurityEventRepository(BaseRepository[SecurityEvent]):
    def __init__(self):
        super().__init__(SecurityEvent)
