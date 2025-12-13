from fastapi import FastAPI

from src.core.middleware.http_audit_log import HTTPAuditLogMiddleware


def handle_middleware(app: FastAPI) -> None:
    app.add_middleware(HTTPAuditLogMiddleware)
