from pydantic import BaseModel, Field, ConfigDict


class CalculateProfitRequest(BaseModel):
    """수익률 계산 요청 DTO"""

    user_id: str = Field(..., description="사용자 UUID")
    exchange_code: int = Field(..., description="거래소 코드 (1:Upbit, 2:Bithumb, 3:Binance, 4:OKX)")
    is_initial: bool = Field(
        default=False, description="최초 fetch 여부 (True: 최초, False: 이후 업데이트)"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "user_id": "bd70f700-5399-46e5-837d-2fc978b3c3b7",
                "exchange_code": 1,
                "is_initial": False,
            }
        }
    )

