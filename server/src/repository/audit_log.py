from src.models.db.audit_log import AuditLog
from src.repository.base import BaseRepository


class AuditLogRepository(BaseRepository[AuditLog]):
    def __init__(self):
        super().__init__(AuditLog)
