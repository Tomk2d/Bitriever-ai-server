from pydantic import BaseModel, Field, ConfigDict


class ArticleExpertRequest(BaseModel):
    """기사 전문가 요청 DTO"""

    target_date: str = Field(..., description="평가하고 싶은 일자 (예: 2019-02-19)")
    days_before: int = Field(
        default=7,
        ge=1,
        le=30,
        description="선택일 포함 과거 며칠까지 헤드라인 사용 (1~30, 기본 7 → 총 8일)",
    )
    max_headlines_per_day: int = Field(
        default=30,
        ge=1,
        le=100,
        description="일자당 최대 헤드라인 개수 (1~100)",
    )
    publisher_type: int | None = Field(
        default=None,
        description="언론사 타입으로 필터 (선택)",
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "target_date": "2019-02-19",
                "days_before": 7,
                "max_headlines_per_day": 30,
                "publisher_type": None,
            }
        }
    )
