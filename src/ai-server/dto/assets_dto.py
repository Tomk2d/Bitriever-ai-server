from pydantic import BaseModel, Field, ConfigDict


class AssetsSyncRequest(BaseModel):
    """자산 동기화 요청 DTO"""

    user_id: str = Field(..., description="사용자 UUID")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "user_id": "bd70f700-5399-46e5-837d-2fc978b3c3b7",
            }
        }
    )

