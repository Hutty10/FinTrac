from typing import Generic, TypeVar

from sqlmodel import SQLModel

from src.repository.base import BaseRepository

T = TypeVar("T", bound=SQLModel)
R = TypeVar("R", bound=BaseRepository)


class BaseService(Generic[T, R]):
    """Base service class to be inherited by specific service implementations"""

    def __init__(self, repository: R):
        self.repository: R = repository