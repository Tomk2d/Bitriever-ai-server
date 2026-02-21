"""매매 1건 분석·평가 메타 에이전트 서비스. 세 전문가 호출 + 해당 건만 포맷 후 trade_evaluation run()."""

import json
import logging
import sys
from concurrent.futures import ThreadPoolExecutor, wait
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path
from typing import Any, List, Optional

from database.database_connection import db

# TradingMind 코드 → 한글 (app-server TradingMind.java와 동일)
TRADING_MIND_CODE_TO_KOREAN = {
    0: "무념무상",
    1: "확신",
    2: "약간 확신",
    3: "기대감",
    11: "욕심",
    12: "조급함",
    13: "불안",
    14: "두려움",
}

_src_dir = Path(__file__).resolve().parent.parent.parent
_ai_agent_dir = _src_dir / "ai-agent"
if _ai_agent_dir.exists() and str(_ai_agent_dir) not in sys.path:
    sys.path.insert(0, str(_ai_agent_dir))

from laboratory.article_ai import ArticleExpertResponse
from laboratory.coin_price_ai import CoinPriceExpertResponse
from laboratory.fear_greed_ai import FearGreedExpertResponse
from laboratory.trade_history_ai import run as run_trade_evaluation_agent
from laboratory.trade_history_ai import TradeEvaluationExpertResponse

from utils.openai_retry import with_openai_retry

logger = logging.getLogger(__name__)


@dataclass
class TradeEvaluationFullResult:
    """매매 분석 API 최종 응답: 세 전문가 응답 + 메타 에이전트 응답."""

    article_expert: ArticleExpertResponse
    coin_price_expert: CoinPriceExpertResponse
    fear_greed_expert: FearGreedExpertResponse
    trade_evaluation: TradeEvaluationExpertResponse


def _expert_response_to_summary(verdict: str, market_flow_analysis: str, short_long_term_perspective: str) -> str:
    """전문가 응답을 verdict + market_flow_analysis + short_long_term_perspective 요약 문자열로 변환."""
    return f"verdict: {verdict}\nmarket_flow_analysis: {market_flow_analysis}\nshort_long_term_perspective: {short_long_term_perspective}"


def _extract_text_from_diary_content(content: Any) -> str:
    """매매 일지 content(JSONB). type이 text인 블록의 content만 추출해 이어 붙인 문자열 반환."""
    if content is None:
        return ""
    try:
        data = json.loads(content) if isinstance(content, str) else content
        blocks = data.get("blocks") or []
        parts = [
            b.get("content", "").strip()
            for b in blocks
            if isinstance(b, dict) and b.get("type") == "text" and b.get("content")
        ]
        return "\n".join(parts).strip() if parts else ""
    except (json.JSONDecodeError, TypeError):
        return ""


def _trading_mind_code_to_korean(code: Optional[int]) -> str:
    """trading_mind 코드를 한글 라벨로 변환."""
    if code is None:
        return "(미기입)"
    return TRADING_MIND_CODE_TO_KOREAN.get(code, "(미기입)")


def _format_trades_from_histories(histories: List) -> str:
    """DB 조회된 매매 내역 리스트를 노트북 get_trades_for_evaluation과 동일한 한 줄 형식 문자열로 변환."""
    lines = []
    for r in histories:
        side = "매도" if r.trade_type == 1 else "매수"
        ts = r.trade_time.strftime("%Y-%m-%d %H:%M:%S") if hasattr(r.trade_time, "strftime") else str(r.trade_time)
        price = float(r.price) if isinstance(r.price, Decimal) else r.price
        qty = float(r.quantity) if isinstance(r.quantity, Decimal) else r.quantity
        total = float(r.total_price) if isinstance(r.total_price, Decimal) else r.total_price
        fee = float(r.fee) if isinstance(r.fee, Decimal) else (r.fee or 0)
        row_str = f"{ts} | {side} | {price} | {qty} | {total} | 수수료 {fee}"
        if r.trade_type == 1:
            if r.profit_loss_rate is not None:
                plr = float(r.profit_loss_rate) if isinstance(r.profit_loss_rate, Decimal) else r.profit_loss_rate
                row_str += f" | 손익률 {plr}%"
            if getattr(r, "avg_buy_price", None) is not None and r.avg_buy_price is not None:
                avg = float(r.avg_buy_price) if isinstance(r.avg_buy_price, Decimal) else r.avg_buy_price
                row_str += f" | 평균매수가 {avg}"
        lines.append(row_str)
    return "\n".join(lines) if lines else "(매매 내역 없음)"


class TradeEvaluationAgentService:
    """매매 1건 분석·평가 메타 에이전트 서비스. 지정한 매매 1건에 대해 세 전문가 의견을 반영해 평가합니다."""

    def __init__(
        self,
        article_agent_service,
        coin_price_agent_service,
        fear_greed_agent_service,
        trading_histories_repository,
        diary_repository,
    ):
        self._article = article_agent_service
        self._coin_price = coin_price_agent_service
        self._fear_greed = fear_greed_agent_service
        self._trading_repo = trading_histories_repository
        self._diary_repo = diary_repository

    def evaluate(
        self,
        user_id: str,
        trade_id: int,
        target_date: str,
        coin_id: int,
    ) -> Optional[TradeEvaluationFullResult]:
        """
        매매 내역 1건(trade_id)에 대해, 선택된 날짜(target_date) 기준 시장 의견(기사·코인가격·공포탐욕)을 조회한 뒤
        메타 에이전트로 해당 1건에 대한 분석·평가를 반환합니다.

        - trade_id에 해당하는 건이 user_id 소유가 아니면 None 반환(호출부에서 404 처리).
        - target_date는 요청에서 받은 선택된 날짜(단일)로, 전문가 호출 및 평가 기간 표시에 사용.
        """
        session = None
        try:
            session = db.get_session()
            trade = self._trading_repo.find_by_user_id_and_id(session, user_id, trade_id)
            diary = self._diary_repo.find_by_trading_history_id(session, trade_id) if trade else None
        finally:
            if session:
                session.close()

        if trade is None:
            return None

        target_period = target_date
        trade_history_text = _format_trades_from_histories([trade])

        diary_trading_mind_text = "(미기입)"
        diary_reason_text = "(매매 일지 없음)"
        if diary is not None:
            diary_trading_mind_text = _trading_mind_code_to_korean(diary.trading_mind)
            diary_reason_text = _extract_text_from_diary_content(diary.content) or "(작성 내용 없음)"

        # 세 전문가 에이전트 병렬 호출 (429 시 재시도 적용)
        run_article = with_openai_retry(self._article.run_article_expert)
        run_coin_price = with_openai_retry(self._coin_price.run_coin_price)
        run_fear_greed = with_openai_retry(self._fear_greed.run_fear_greed)
        with ThreadPoolExecutor(max_workers=3) as executor:
            f_article = executor.submit(run_article, target_date=target_date)
            f_coin_price = executor.submit(
                run_coin_price,
                target_date=target_date,
                coin_id=coin_id,
            )
            f_fear_greed = executor.submit(run_fear_greed, target_date=target_date)
            wait([f_article, f_coin_price, f_fear_greed])
            article_resp = f_article.result()
            coin_price_resp = f_coin_price.result()
            fear_greed_resp = f_fear_greed.result()

        expert_article_summary = _expert_response_to_summary(
            article_resp.verdict,
            article_resp.market_flow_analysis,
            article_resp.short_long_term_perspective,
        )
        expert_coin_price_summary = _expert_response_to_summary(
            coin_price_resp.verdict,
            coin_price_resp.market_flow_analysis,
            coin_price_resp.short_long_term_perspective,
        )
        expert_fear_greed_summary = _expert_response_to_summary(
            fear_greed_resp.verdict,
            fear_greed_resp.market_flow_analysis,
            fear_greed_resp.short_long_term_perspective,
        )

        # 메타 에이전트 호출 (3개 결과 종합, 429 시 재시도 적용)
        run_meta = with_openai_retry(run_trade_evaluation_agent)
        trade_eval_resp = run_meta(
            target_period=target_period,
            expert_article_summary=expert_article_summary,
            expert_coin_price_summary=expert_coin_price_summary,
            expert_fear_greed_summary=expert_fear_greed_summary,
            trade_history_text=trade_history_text,
            diary_trading_mind=diary_trading_mind_text,
            diary_reason=diary_reason_text,
        )

        return TradeEvaluationFullResult(
            article_expert=article_resp,
            coin_price_expert=coin_price_resp,
            fear_greed_expert=fear_greed_resp,
            trade_evaluation=trade_eval_resp,
        )
