from fastapi import APIRouter, HTTPException, Depends
from typing import Annotated, Any
import logging
import re

from dto.http_response import ErrorResponse, SuccessResponse
from dto.coin_price_dto import CoinPriceRequest
from dependencies import get_coin_price_agent_service

router = APIRouter(prefix="/coin-price", tags=["코인가격전문가 응답 확인용"])
logger = logging.getLogger(__name__)

_DATE_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}$")


@router.post("/analyze", summary="코인 가격 전문가 분석")
async def analyze_coin_price(
    request: CoinPriceRequest,
    coin_price_service: Annotated[Any, Depends(get_coin_price_agent_service)],
):
    """
    평가 일자에 대해 코인 가격(시고저종·등락률) 기반 매수/매도 판단 의견을 반환합니다.

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

        response = coin_price_service.run_coin_price(
            target_date=request.target_date,
            months_before=request.months_before,
            market_code=request.market_code,
        )
        return SuccessResponse(
            data=response.model_dump(),
            message="코인 가격 분석이 완료되었습니다",
        )

    except HTTPException:
        raise
    except ValueError as e:
        logger.warning(f"코인 가격 분석 검증 에러: {e}")
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
        logger.exception("코인 가격 분석 중 예상치 못한 에러")
        raise HTTPException(
            status_code=500,
            detail=ErrorResponse(
                status_code=500,
                error_code="INTERNAL_SERVER_ERROR",
                message="서버 내부 오류가 발생했습니다",
                details=str(e),
            ).dict(),
        )
