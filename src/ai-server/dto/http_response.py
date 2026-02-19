from pydantic import BaseModel, Field
from typing import Optional, Any
from datetime import datetime


class ErrorResponse(BaseModel):
    """에러 응답을 위한 DTO"""

    success: bool = False
    status_code: int
    error_code: str
    message: str
    details: Optional[Any] = None
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())


class SuccessResponse(BaseModel):
    """성공 응답을 위한 DTO"""

    success: bool = True
    status_code: int = 200
    data: Any
    message: Optional[str] = None
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
