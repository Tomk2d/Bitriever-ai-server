from fastapi import APIRouter, HTTPException, Depends
from typing import Annotated, Any
import logging
import re

from dto.http_response import ErrorResponse, SuccessResponse
from dto.fear_greed_dto import FearGreedRequest
from dependencies import get_fear_greed_agent_service

router = APIRouter(prefix="/fear-greed", tags=["공포탐욕지수 응답 확인용"])
logger = logging.getLogger(__name__)

# YYYY-MM-DD 형식
_DATE_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}$")


@router.post("/analyze", summary="공포/탐욕 지수 전문가 분석")
async def analyze_fear_greed(
    request: FearGreedRequest,
    fear_greed_service: Annotated[Any, Depends(get_fear_greed_agent_service)],
):
    """
    평가 일자에 대해 공포/탐욕 지수 기반 매수/매도 판단 의견을 반환합니다.

    - target_date: 평가하고 싶은 일자 (YYYY-MM-DD)
    - months_before: 해당 일자 이전 몇 개월 데이터를 사용할지 (기본 6)
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

        response = fear_greed_service.run_fear_greed(
            target_date=request.target_date,
            months_before=request.months_before,
        )
        return SuccessResponse(
            data=response.model_dump(),
            message="공포/탐욕 지수 분석이 완료되었습니다",
        )

    except HTTPException:
        raise
    except ValueError as e:
        logger.warning(f"공포/탐욕 분석 검증 에러: {e}")
        raise HTTPException(
            status_code=400,
            detail=ErrorResponse(
                status_code=400,
                error_code="VALIDATION_ERROR",
                message=str(e),
                details="입력된 날짜 또는 기간을 확인해주세요",
            ).dict(),
        )
    except Exception as e:
        logger.exception("공포/탐욕 지수 분석 중 예상치 못한 에러")
        raise HTTPException(
            status_code=500,
            detail=ErrorResponse(
                status_code=500,
                error_code="INTERNAL_SERVER_ERROR",
                message="서버 내부 오류가 발생했습니다",
                details=str(e),
            ).dict(),
        )
