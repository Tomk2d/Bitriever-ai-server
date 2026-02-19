from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from enum import Enum


class ExchangeProvider(int, Enum):
    """거래소 제공자 Enum"""

    UPBIT = 1  # 업비트
    BITHUMB = 2  # 빗썸
    BINANCE = 3  # 바이낸스
    OKX = 4  # OKX


class ExchangeCredentialsRequest(BaseModel):
    """거래소 자격증명 요청 DTO"""

    exchange_provider: ExchangeProvider = Field(..., description="거래소 제공자")
    access_key: str = Field(..., min_length=1, description="액세스 키")
    secret_key: str = Field(..., min_length=1, description="시크릿 키")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "exchange_provider": 1,
                "access_key": "your_access_key_here",
                "secret_key": "your_secret_key_here",
            }
        }
    )


class ExchangeCredentialsResponse(BaseModel):
    """거래소 자격증명 응답 DTO"""

    user_id: str = Field(..., description="사용자 UUID")
    exchange_provider: ExchangeProvider = Field(..., description="거래소 제공자")
    provider_name: str = Field(..., description="거래소 제공자 이름")
    created_at: str = Field(..., description="생성 시간")
    last_updated_at: Optional[str] = Field(None, description="마지막 업데이트 시간")
    # 복호화된 키 필드 추가
    access_key: Optional[str] = Field(None, description="복호화된 액세스 키")
    secret_key: Optional[str] = Field(None, description="복호화된 시크릿 키")

    @classmethod
    def from_credentials(cls, credentials):
        """ExchangeCredentials 모델에서 응답 생성"""
        return cls(
            user_id=str(credentials.user_id),
            exchange_provider=ExchangeProvider(credentials.exchange_provider),
            provider_name=credentials.provider_name,
            created_at=(
                credentials.created_at.isoformat()
                if credentials.created_at
                else "2024-01-01T00:00:00"
            ),
            last_updated_at=(
                credentials.last_updated_at.isoformat()
                if credentials.last_updated_at
                else None
            ),
            access_key=None,  # 기본값은 None
            secret_key=None,  # 기본값은 None
        )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "user_id": "123e4567-e89b-12d3-a456-426614174000",
                "exchange_provider": 1,
                "provider_name": "UPBIT",
                "created_at": "2024-01-01T00:00:00",
                "last_updated_at": "2024-01-01T00:00:00",
                "access_key": "your_access_key_here",
                "secret_key": "your_secret_key_here",
            }
        }
    )
