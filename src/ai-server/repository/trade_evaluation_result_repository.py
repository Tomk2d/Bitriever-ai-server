import logging
import uuid
from typing import Any, Dict, List, Optional

from database.database_connection import db
from model.TradeEvaluationResult import TradeEvaluationResult


class TradeEvaluationResultRepository:
    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def save(
        self,
        session: Any,
        user_id: str,
        trade_id: int,
        target_date: str,
        coin_id: int,
        result_dict: Dict[str, Any],
    ) -> TradeEvaluationResult:
        """(user_id, trade_id) 기준 upsert: 있으면 갱신, 없으면 INSERT."""
        from datetime import date

        user_uuid = uuid.UUID(user_id) if isinstance(user_id, str) else user_id
        target_dt = (
            date.fromisoformat(target_date)
            if isinstance(target_date, str)
            else target_date
        )
        row = self.find_by_user_id_and_trade_id(session, user_id, trade_id)
        if row:
            row.target_date = target_dt
            row.coin_id = coin_id
            row.result = result_dict
            session.flush()
            session.refresh(row)
            return row
        row = TradeEvaluationResult(
            user_id=user_uuid,
            trade_id=trade_id,
            target_date=target_dt,
            coin_id=coin_id,
            result=result_dict,
        )
        session.add(row)
        session.flush()
        session.refresh(row)
        return row

    def find_by_user_id_and_trade_id(
        self, session: Any, user_id: str, trade_id: int
    ) -> Optional[TradeEvaluationResult]:
        """(user_id, trade_id)로 1건 조회. 없으면 None."""
        user_uuid = uuid.UUID(user_id) if isinstance(user_id, str) else user_id
        return (
            session.query(TradeEvaluationResult)
            .filter(
                TradeEvaluationResult.user_id == user_uuid,
                TradeEvaluationResult.trade_id == trade_id,
            )
            .first()
        )

    def find_by_trade_id(
        self, session: Any, trade_id: int
    ) -> Optional[TradeEvaluationResult]:
        """trade_id로 1건 조회. 최신(created_at 내림) 1건 반환. 없으면 None."""
        return (
            session.query(TradeEvaluationResult)
            .filter(TradeEvaluationResult.trade_id == trade_id)
            .order_by(TradeEvaluationResult.created_at.desc())
            .first()
        )

    def find_all_by_trade_id(
        self, session: Any, trade_id: int
    ) -> List[TradeEvaluationResult]:
        """trade_id로 전체 목록 조회 (최신순)."""
        return (
            session.query(TradeEvaluationResult)
            .filter(TradeEvaluationResult.trade_id == trade_id)
            .order_by(TradeEvaluationResult.created_at.desc())
            .all()
        )
