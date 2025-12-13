from typing import Any, Generic, TypeVar

from src.models.schemas.base import BaseSchemaModel

T = TypeVar("T")


class ResponseModel(BaseSchemaModel, Generic[T]):
    success: bool = True
    message: str
    data: T | None
    errors: dict[str, Any] | None = None
    meta: dict[str, Any] | None = None
