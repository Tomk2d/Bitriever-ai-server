from pydantic import BaseModel
from typing import Optional, Any
from datetime import datetime


class ErrorResponse(BaseModel):
    """에러 응답을 위한 DTO"""

    success: bool = False
    status_code: int
    error_code: str
    message: str
    details: Optional[Any] = None
    timestamp: datetime = datetime.now()


class SuccessResponse(BaseModel):
    """성공 응답을 위한 DTO"""

    success: bool = True
    status_code: int = 200
    data: Any
    message: Optional[str] = None
    timestamp: datetime = datetime.now()


class UpbitAPIException(Exception):
    """Upbit API 관련 예외"""

    def __init__(
        self,
        message: str,
        error_code: str = "UPBIT_API_ERROR",
        details: Any = None,
        status_code: int = 400,
    ):
        self.message = message
        self.error_code = error_code
        self.details = details
        self.status_code = status_code
        super().__init__(self.message)


class AuthenticationException(Exception):
    """인증 관련 예외"""

    def __init__(
        self,
        message: str = "인증에 실패했습니다",
        error_code: str = "AUTH_ERROR",
        status_code: int = 401,
    ):
        self.message = message
        self.error_code = error_code
        self.status_code = status_code
        super().__init__(self.message)


class ValidationException(Exception):
    """검증 관련 예외"""

    def __init__(
        self,
        message: str,
        error_code: str = "VALIDATION_ERROR",
        details: Any = None,
        status_code: int = 400,
    ):
        self.message = message
        self.error_code = error_code
        self.details = details
        self.status_code = status_code
        super().__init__(self.message)


class RateLimitException(Exception):
    """Rate Limit 관련 예외"""

    def __init__(
        self,
        message: str = "요청 한도를 초과했습니다",
        error_code: str = "RATE_LIMIT_ERROR",
        status_code: int = 429,
    ):
        self.message = message
        self.error_code = error_code
        self.status_code = status_code
        super().__init__(self.message)
