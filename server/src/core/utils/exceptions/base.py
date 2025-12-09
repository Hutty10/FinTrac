from fastapi import HTTPException


class BaseAppException(HTTPException):
    def __init__(
        self,
        message: str,
        status_code: int,
        errors: dict[str, str] | None = None,
        headers: dict[str, str] | None = None,
    ):
        self.message = message
        self.errors = errors
        super().__init__(status_code=status_code, detail=message, headers=headers)
