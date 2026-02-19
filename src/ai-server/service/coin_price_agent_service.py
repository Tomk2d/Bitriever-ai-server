"""코인 가격 전문가 에이전트를 호출하는 서비스. API 경로에서는 DB만 사용."""

import logging
import sys
from datetime import datetime, timedelta
from decimal import Decimal
from pathlib import Path

from database.database_connection import db

_src_dir = Path(__file__).resolve().parent.parent.parent
_ai_agent_dir = _src_dir / "ai-agent"
if _ai_agent_dir.exists() and str(_ai_agent_dir) not in sys.path:
    sys.path.insert(0, str(_ai_agent_dir))

from laboratory.coin_price_ai import run as run_coin_price_agent
from laboratory.coin_price_ai import CoinPriceExpertResponse

logger = logging.getLogger(__name__)

DEFAULT_MARKET_CODE = "KRW-BTC"


class CoinPriceAgentService:
    """코인 가격 전문가 에이전트 서비스."""

    def __init__(self, coin_price_day_repository, default_market_code: str = DEFAULT_MARKET_CODE):
        self._coin_price_day_repository = coin_price_day_repository
        self._default_market_code = default_market_code

    def run_coin_price(
        self,
        target_date: str,
        months_before: int = 6,
        coin_id: int | None = None,
        market_code: str | None = None,
    ) -> CoinPriceExpertResponse:
        """
        평가 일자에 대해 코인 가격 전문가 의견을 반환합니다. DB에서 기간 데이터 조회 후 에이전트에 전달.
        coin_id가 있으면 coin_id로 조회, 없으면 market_code(기본 KRW-BTC)로 조회.
        """
        target = datetime.strptime(target_date, "%Y-%m-%d")
        start_dt = (target - timedelta(days=months_before * 30)).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        end_dt = (target + timedelta(days=1)).replace(
            hour=0, minute=0, second=0, microsecond=0
        )

        session = None
        try:
            session = db.get_session()
            if coin_id is not None:
                rows = self._coin_price_day_repository.find_by_coin_id_and_date_range(
                    session, coin_id, start_dt, end_dt
                )
            else:
                market_code = market_code or self._default_market_code
                rows = self._coin_price_day_repository.find_by_market_code_and_date_range(
                    session, market_code, start_dt, end_dt
                )
            lines = []
            for row in rows:
                d = row.candle_date_time_utc
                if hasattr(d, "date"):
                    d = d.date()
                day_str = d.strftime("%Y-%m-%d") if hasattr(d, "strftime") else str(d)
                o = float(row.opening_price) if isinstance(row.opening_price, Decimal) else row.opening_price
                h = float(row.high_price) if isinstance(row.high_price, Decimal) else row.high_price
                l = float(row.low_price) if isinstance(row.low_price, Decimal) else row.low_price
                c = float(row.trade_price) if isinstance(row.trade_price, Decimal) else row.trade_price
                rate = float(row.change_rate) if isinstance(row.change_rate, Decimal) else row.change_rate
                pct_str = f"{rate:+.2%}" if rate is not None else "N/A"
                lines.append(f"{day_str}: {o:.0f} | {h:.0f} | {l:.0f} | {c:.0f}, {pct_str}")
            period_data = "\n".join(lines)
            return run_coin_price_agent(
                target_date=target_date,
                months_before=months_before,
                period_data=period_data,
            )
        finally:
            if session:
                session.close()
