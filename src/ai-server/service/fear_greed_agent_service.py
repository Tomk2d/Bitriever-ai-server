"""공포/탐욕 지수 전문가 에이전트를 호출하는 서비스. API 경로에서는 DB만 사용."""

import logging
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

from database.database_connection import db

# ai-agent(laboratory) import
_src_dir = Path(__file__).resolve().parent.parent.parent
_ai_agent_dir = _src_dir / "ai-agent"
if _ai_agent_dir.exists() and str(_ai_agent_dir) not in sys.path:
    sys.path.insert(0, str(_ai_agent_dir))

from laboratory.fear_greed_ai import run as run_fear_greed_agent
from laboratory.fear_greed_ai import FearGreedExpertResponse

logger = logging.getLogger(__name__)


class FearGreedAgentService:
    """공포/탐욕 지수 전문가 에이전트 서비스."""

    def __init__(self, fear_greed_index_repository):
        self._fear_greed_index_repository = fear_greed_index_repository

    def run_fear_greed(
        self, target_date: str, months_before: int = 6
    ) -> FearGreedExpertResponse:
        """
        평가 일자에 대해 공포/탐욕 전문가 의견을 반환합니다. DB에서 기간 데이터 조회 후 에이전트에 전달.
        """
        target = date.fromisoformat(target_date)
        start_date = target - timedelta(days=months_before * 30)
        end_date = target

        session = None
        try:
            session = db.get_session()
            rows = self._fear_greed_index_repository.find_by_date_range(
                session, start_date, end_date
            )
            period_data = "\n".join(
                f"{d.isoformat()}: {v}" for d, v in rows
            )
            return run_fear_greed_agent(
                target_date=target_date,
                months_before=months_before,
                period_data=period_data,
            )
        finally:
            if session:
                session.close()
