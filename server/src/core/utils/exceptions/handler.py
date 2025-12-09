import logging

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.requests import Request
from fastapi.responses import JSONResponse

from src.config.manager import settings
from src.core.utils.exceptions.base import BaseAppException

logger = logging.getLogger(__name__)


def handle_exceptions(app: FastAPI):
    @app.exception_handler(BaseAppException)
    async def base_app_exception_handler(request: Request, exc: BaseAppException):
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "success": False,
                "message": exc.message,
                "data": None,
                "errors": getattr(exc, "errors", None),
                "meta": None,
            },
        )

    @app.exception_handler(Exception)
    async def generic_exception_handler(request: Request, exc: Exception):
        logger.error(f"Unhandled exception: {exc}", exc_info=True)

        error_detail = str(exc) if settings.DEBUG else "Internal server error"

        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "message": "Internal server error",
                "data": None,
                "errors": {"detail": error_detail},
                "meta": None,
            },
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request, exc: RequestValidationError
    ):
        errors = {}
        error_messages = []

        for error in exc.errors():
            field = error["loc"][-1]
            message = error["msg"]
            errors[field] = message
            error_messages.append(f"{field}: {message}")

        message = " | ".join(error_messages)

        return JSONResponse(
            status_code=422,
            content={
                "success": False,
                "message": message,
                "data": None,
                "errors": errors,
                "meta": None,
            },
        )
