"""매매 1건 분석·평가 메타 에이전트 API."""

import logging
import re
from typing import Any, Annotated

from fastapi import APIRouter, Depends, HTTPException

from database.database_connection import db
from dto.http_response import ErrorResponse, SuccessResponse
from dto.trade_evaluation_dto import TradeEvaluationRequest
from dependencies import (
    get_trade_evaluation_agent_service,
    get_trade_evaluation_result_repository,
)

router = APIRouter(prefix="/trade-evaluation", tags=["매매평가"])
logger = logging.getLogger(__name__)

_DATE_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}$")


@router.post("/evaluate", summary="매매 1건 분석·평가")
async def evaluate_one_trade(
    request: TradeEvaluationRequest,
    trade_evaluation_service: Annotated[Any, Depends(get_trade_evaluation_agent_service)],
    trade_evaluation_result_repository: Annotated[
        Any, Depends(get_trade_evaluation_result_repository)
    ],
):
    """
    지정한 매매 내역 1건(trade_id)에 대해, 선택된 날짜(target_date) 기준 시장 의견(기사·코인가격·공포탐욕)을 반영해
    메타 에이전트로 분석·평가 결과를 반환합니다. **매매 1건** + **선택된 날짜** 단일로 평가합니다.
    """
    try:
        if not _DATE_PATTERN.match(request.target_date):
            raise HTTPException(
                status_code=400,
                detail=ErrorResponse(
                    status_code=400,
                    error_code="INVALID_DATE_FORMAT",
                    message="날짜 형식이 올바르지 않습니다",
                    details="target_date는 YYYY-MM-DD 형식이어야 합니다 (예: 2022-01-14)",
                ).dict(),
            )
        response = trade_evaluation_service.evaluate(
            user_id=request.user_id,
            trade_id=request.trade_id,
            target_date=request.target_date,
            coin_id=request.coin_id,
        )
        if response is None:
            raise HTTPException(
                status_code=404,
                detail=ErrorResponse(
                    status_code=404,
                    error_code="TRADE_NOT_FOUND",
                    message="해당 매매 내역을 찾을 수 없습니다",
                    details="user_id와 trade_id에 해당하는 거래가 없거나 권한이 없습니다",
                ).dict(),
            )
        data = {
            "article_expert": response.article_expert.model_dump(),
            "coin_price_expert": response.coin_price_expert.model_dump(),
            "fear_greed_expert": response.fear_greed_expert.model_dump(),
            "trade_evaluation_expert": response.trade_evaluation.model_dump(),
        }
        session = db.get_session()
        try:
            trade_evaluation_result_repository.save(
                session,
                user_id=request.user_id,
                trade_id=request.trade_id,
                target_date=request.target_date,
                coin_id=request.coin_id,
                result_dict=data,
            )
            session.commit()
            saved = trade_evaluation_result_repository.find_by_trade_id(
                session, request.trade_id
            )
            data_to_return = saved.result if saved else data
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()
        return SuccessResponse(
            data=data_to_return,
            message="매매 1건 분석·평가가 완료되었습니다",
        )
    except HTTPException:
        raise
    except ValueError as e:
        logger.warning("매매 평가 검증 에러: %s", e)
        raise HTTPException(
            status_code=400,
            detail=ErrorResponse(
                status_code=400,
                error_code="VALIDATION_ERROR",
                message=str(e),
                details="입력값을 확인해주세요",
            ).dict(),
        )
    except Exception as e:
        logger.exception("매매 분석·평가 중 예상치 못한 에러")
        raise HTTPException(
            status_code=500,
            detail=ErrorResponse(
                status_code=500,
                error_code="INTERNAL_SERVER_ERROR",
                message="서버 내부 오류가 발생했습니다",
                details=str(e),
            ).dict(),
        )
