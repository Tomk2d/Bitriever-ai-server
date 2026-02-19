from pydantic import BaseModel, Field, ConfigDict


class TradeEvaluationRequest(BaseModel):
    """매매 1건 분석·평가 요청 DTO. 지정한 매매 내역 1건에 대해 선택된 날짜 기준 전문가 의견을 반영한 평가를 반환합니다."""

    user_id: str = Field(..., description="매매 내역 소유 사용자 ID (UUID)")
    trade_id: int = Field(..., description="분석할 매매 내역 1건의 ID (trading_histories.id)")
    target_date: str = Field(..., description="선택된 날짜 (YYYY-MM-DD). 해당 일자 기준 시장 의견으로 평가합니다.")
    coin_id: int = Field(..., description="코인가격 전문가용 코인 ID (coins.id). 해당 코인의 가격 데이터로 평가합니다.")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "user_id": "550e8400-e29b-41d4-a716-446655440000",
                "trade_id": 123,
                "target_date": "2022-01-14",
                "coin_id": 1,
            }
        }
    )
