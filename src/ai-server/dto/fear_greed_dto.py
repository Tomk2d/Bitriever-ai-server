from pydantic import BaseModel, Field, ConfigDict


class FearGreedRequest(BaseModel):
    """공포/탐욕 지수 전문가 요청 DTO"""

    target_date: str = Field(..., description="평가하고 싶은 일자 (예: 2019-02-19)")
    months_before: int = Field(
        default=6,
        ge=1,
        le=24,
        description="해당 일자 이전 몇 개월 데이터를 사용할지 (1~24)",
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "target_date": "2019-02-19",
                "months_before": 6,
            }
        }
    )
