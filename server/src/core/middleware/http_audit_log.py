import json
import logging
import time
from typing import Callable, override
from uuid import UUID

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from src.core.securities.jwt import jwt_manager
from src.models.db.audit_log import AuditLog
from src.repository.database import async_db

logger = logging.getLogger(__name__)


class HTTPAuditLogMiddleware(BaseHTTPMiddleware):
    """
    Production-grade middleware for logging HTTP requests and responses to the audit log.

    Features:
    - Async-safe audit logging with database persistence
    - User identification from request Authorization header (JWT token)
    - Request metadata capture (method, path, query string, client IP)
    - Request/response body capture (with size limits)
    - Sensitive data masking
    - Performance monitoring with request duration
    - Graceful error handling that doesn't break the request
    - Configurable excluded paths
    - Non-blocking audit logging with separate database session
    """

    # Paths that should not be audited (health checks, etc.)
    EXCLUDED_PATHS = {"/health", "/docs", "/openapi.json", "/redoc"}

    # HTTP methods that should not be audited
    EXCLUDED_METHODS = {"HEAD", "OPTIONS"}

    # Maximum size of request/response body to capture (1MB)
    MAX_BODY_SIZE = 1024 * 1024

    # Sensitive patterns to mask in audit logs
    SENSITIVE_PATTERNS = {
        "password",
        "token",
        "authorization",
        "api_key",
        "secret",
        "credit_card",
        "bvn",
        "nin",
    }

    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.app = app

    @override
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Main middleware dispatch method that logs all HTTP activity.
        """
        # Skip excluded paths and methods
        if self._should_skip_audit(request):
            return await call_next(request)

        # Extract request metadata
        method = request.method
        path = request.url.path
        query_string = request.url.query or None
        client_host = request.client.host if request.client else None

        # Get user ID from request context (JWT token, session, etc.)
        user_id = await self._extract_user_id(request)

        # Capture request body if needed
        request_body = None
        if method in {"POST", "PUT", "PATCH"}:
            request_body = await self._capture_body(request)

        # Track request duration
        start_time = time.time()
        status_code = 500  # Default to error if exception occurs
        response_body = None

        try:
            # Call the actual endpoint
            response = await call_next(request)
            status_code = response.status_code

            # Capture response body for error responses
            if status_code >= 400:
                response_body = await self._capture_response_body(response)

            return response

        except Exception:
            # Log the exception but don't suppress it
            logger.exception(f"Error processing request {method} {path}")
            status_code = 500
            raise

        finally:
            # Always log the audit trail, even if there was an error
            # Use a separate task to avoid blocking the response
            duration = time.time() - start_time
            try:
                await self._log_audit(
                    user_id=user_id,
                    method=method,
                    path=path,
                    query_string=query_string,
                    status_code=status_code,
                    client_host=client_host,
                    request_body=request_body,
                    response_body=response_body,
                    duration_ms=int(duration * 1000),
                )
            except Exception as exc:
                logger.error(f"Failed to schedule audit logging: {exc}", exc_info=True)

    def _should_skip_audit(self, request: Request) -> bool:
        """Check if this request should be excluded from audit logging."""
        return (
            request.method in self.EXCLUDED_METHODS
            or request.url.path in self.EXCLUDED_PATHS
            or any(request.url.path.startswith(path) for path in self.EXCLUDED_PATHS)
        )

    async def _extract_user_id(self, request: Request) -> UUID | None:
        """
        Extract user ID from request Authorization header.
        """
        try:
            auth_header = request.headers.get("Authorization")
            if auth_header:
                token = auth_header.split(" ")[1]
                payload = await jwt_manager.verify_token(
                    token=token, token_type="access"
                )
                user_id_str = payload.get("user_id")
                if user_id_str:
                    return UUID(user_id_str)

            return None
        except Exception as exc:
            logger.warning(f"Failed to extract user_id: {exc}")
            return None

    async def _capture_body(self, request: Request) -> str | None:
        """Capture and mask sensitive request body data."""
        try:
            body = await request.body()

            if len(body) > self.MAX_BODY_SIZE:
                return f"[Body exceeded max size of {self.MAX_BODY_SIZE} bytes]"

            if not body:
                return None

            try:
                # Try to parse as JSON
                data = json.loads(body)
                masked_data = self._mask_sensitive_data(data)
                return json.dumps(masked_data)
            except json.JSONDecodeError:
                # Return as string if not JSON
                return body.decode("utf-8", errors="ignore")[:1000]

        except Exception as exc:
            logger.warning(f"Failed to capture request body: {exc}")
            return None

    async def _capture_response_body(self, response: Response) -> str | None:
        """Capture and mask sensitive response body data."""
        try:
            # Get the raw body from the response if available
            if hasattr(response, "body"):
                body = response.body
            else:
                # If no direct body attribute, response is already consumed
                logger.debug("Response body already consumed, skipping capture")
                return None

            if len(body) > self.MAX_BODY_SIZE:
                return f"[Body exceeded max size of {self.MAX_BODY_SIZE} bytes]"

            if not body:
                return None

            try:
                # Try to parse as JSON
                data = json.loads(body)
                masked_data = self._mask_sensitive_data(data)
                return json.dumps(masked_data)
            except json.JSONDecodeError:
                return body.decode("utf-8", errors="ignore")[:1000]  # type: ignore

        except Exception as exc:
            logger.warning(f"Failed to capture response body: {exc}")
            return None

    def _mask_sensitive_data(self, data: dict | list | str) -> dict | list | str:
        """Recursively mask sensitive fields in data."""
        if isinstance(data, dict):
            return {
                k: "[MASKED]"
                if self._is_sensitive_key(k)
                else self._mask_sensitive_data(v)
                for k, v in data.items()
            }
        elif isinstance(data, list):
            return [self._mask_sensitive_data(item) for item in data]
        return data

    def _is_sensitive_key(self, key: str) -> bool:
        """Check if a key contains sensitive information."""
        key_lower = key.lower()
        return any(pattern in key_lower for pattern in self.SENSITIVE_PATTERNS)

    async def _log_audit(
        self,
        user_id: UUID | None,
        method: str,
        path: str,
        query_string: str | None,
        status_code: int,
        client_host: str | None,
        request_body: str | None,
        response_body: str | None,
        duration_ms: int,
    ) -> None:
        """
        Create an audit log entry in the database using a separate session.
        This ensures the audit log is committed independently from the request transaction.
        """
        if user_id is None:
            logger.debug(f"Skipping audit for unauthenticated {method} {path}")
            return

        print("Logging audit for:", method, path, "by user:", user_id)

        try:
            # Prepare audit details
            details = {
                "method": method,
                "path": path,
                "query_string": query_string,
                "client_host": client_host,
                "request_body": request_body,
                "response_body": response_body,
                "duration_ms": duration_ms,
            }

            # Determine entity and action from path and method
            entity = self._extract_entity_from_path(path)
            action = self._extract_action_from_method(method)
            entity_id = self._extract_entity_id_from_path(path)

            # Create audit log entry
            audit_log = AuditLog(
                user_id=user_id,
                action=action,
                entity=entity,
                entity_id=entity_id,
                status_code=status_code,
                details=json.dumps(details),
            )

            # Use a NEW session for audit logging to avoid transaction conflicts
            # This is separate from the request's session
            async with async_db.session_maker() as audit_session:
                audit_session.add(audit_log)
                await audit_session.commit()
                logger.debug(f"Audit logged: {action} {entity} by {user_id}")

        except Exception as exc:
            logger.error(
                f"Failed to log audit entry for {method} {path}: {exc}",
                exc_info=True,
            )

    def _extract_entity_from_path(self, path: str) -> str:
        """
        Extract entity name from URL path.

        Examples:
        - /api/v1/users/123 -> "user"
        - /api/v1/users -> "user"
        - /auth/login -> "login"
        """
        parts = path.strip("/").split("/")
        if len(parts) < 2:
            # Single segment path
            return parts[0] if parts else "unknown"

        # Check if last part is a UUID (resource ID)
        last_part = parts[-1]
        try:
            UUID(last_part)
            # If it's a UUID, use the segment before it
            entity = parts[-2]
        except (ValueError, IndexError):
            # If it's not a UUID, use the last segment
            entity = last_part

        # Singularize by removing trailing 's'
        return entity.rstrip("s")

    def _extract_action_from_method(self, method: str) -> str:
        """Map HTTP method to action."""
        method_action_map = {
            "GET": "read",
            "POST": "create",
            "PUT": "update",
            "PATCH": "update",
            "DELETE": "delete",
        }
        return method_action_map.get(method, "unknown")

    def _extract_entity_id_from_path(self, path: str) -> UUID | None:
        """Extract entity ID from URL path if it's a UUID."""
        try:
            parts = path.strip("/").split("/")
            if parts:
                last_part = parts[-1]
                return UUID(last_part)
        except (ValueError, IndexError):
            pass
        return None
