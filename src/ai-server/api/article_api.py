from fastapi import APIRouter, HTTPException, Depends
from typing import Annotated, Any
import logging
import re

from dto.http_response import ErrorResponse, SuccessResponse
from dto.article_dto import ArticleExpertRequest
from dependencies import get_article_agent_service

router = APIRouter(prefix="/article", tags=["기사전문가 응답 확인용"])
logger = logging.getLogger(__name__)

_DATE_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}$")


@router.post("/analyze", summary="기사(헤드라인) 전문가 분석")
async def analyze_article(
    request: ArticleExpertRequest,
    article_service: Annotated[Any, Depends(get_article_agent_service)],
):
    """
    평가 일자에 대해 해당 일 전후 기사 헤드라인 기반 시장 분위기·이슈 해석 및 매수/매도 관점 의견을 반환합니다.

    - target_date: 평가하고 싶은 일자 (YYYY-MM-DD)
    - days_before: 선택일 포함 과거 며칠까지 사용 (기본 7 → 총 8일)
    - max_headlines_per_day: 일자당 최대 헤드라인 개수 (기본 30)
    """
    try:
        if not _DATE_PATTERN.match(request.target_date):
            raise HTTPException(
                status_code=400,
                detail=ErrorResponse(
                    status_code=400,
                    error_code="INVALID_DATE_FORMAT",
                    message="날짜 형식이 올바르지 않습니다",
                    details="target_date는 YYYY-MM-DD 형식이어야 합니다 (예: 2019-02-19)",
                ).dict(),
            )

        response = article_service.run_article_expert(
            target_date=request.target_date,
            days_before=request.days_before,
            max_headlines_per_day=request.max_headlines_per_day,
            publisher_type=request.publisher_type,
        )
        return SuccessResponse(
            data=response.model_dump(),
            message="기사 헤드라인 분석이 완료되었습니다",
        )

    except HTTPException:
        raise
    except ValueError as e:
        logger.warning(f"기사 분석 검증 에러: {e}")
        raise HTTPException(
            status_code=400,
            detail=ErrorResponse(
                status_code=400,
                error_code="VALIDATION_ERROR",
                message=str(e),
                details="입력된 날짜 또는 옵션을 확인해주세요",
            ).dict(),
        )
    except Exception as e:
        logger.exception("기사 헤드라인 분석 중 예상치 못한 에러")
        raise HTTPException(
            status_code=500,
            detail=ErrorResponse(
                status_code=500,
                error_code="INTERNAL_SERVER_ERROR",
                message="서버 내부 오류가 발생했습니다",
                details=str(e),
            ).dict(),
        )
