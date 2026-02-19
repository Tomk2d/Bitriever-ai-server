"""기사(헤드라인) 전문가 에이전트를 호출하는 서비스. API 경로에서는 DB만 사용."""

import logging
import sys
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

from database.database_connection import db

_src_dir = Path(__file__).resolve().parent.parent.parent
_ai_agent_dir = _src_dir / "ai-agent"
if _ai_agent_dir.exists() and str(_ai_agent_dir) not in sys.path:
    sys.path.insert(0, str(_ai_agent_dir))

from laboratory.article_ai import run as run_article_agent
from laboratory.article_ai import ArticleExpertResponse

logger = logging.getLogger(__name__)


class ArticleAgentService:
    """기사(헤드라인) 전문가 에이전트 서비스."""

    def __init__(self, article_repository):
        self._article_repository = article_repository

    def run_article_expert(
        self,
        target_date: str,
        days_before: int = 7,
        max_headlines_per_day: int = 30,
        publisher_type: Optional[int] = None,
    ) -> ArticleExpertResponse:
        """
        평가 일자에 대해 기사 헤드라인 기반 시장 분위기·이슈 의견을 반환합니다.
        DB에서 headline, published_at, original_url 조회 후 period_data에 URL 포함해 에이전트에 전달.
        """
        target = datetime.strptime(target_date, "%Y-%m-%d")
        end_dt = target.replace(hour=23, minute=59, second=59, microsecond=999999)
        start_dt = (target - timedelta(days=days_before)).replace(
            hour=0, minute=0, second=0, microsecond=0
        )

        session = None
        try:
            session = db.get_session()
            articles = self._article_repository.find_by_published_at_between(
                session, start_dt, end_dt, publisher_type=publisher_type
            )
            by_date = defaultdict(list)
            for a in articles:
                d = a.published_at.date() if a.published_at else None
                if d is not None:
                    by_date[d].append((a.headline or "", a.original_url or ""))

            lines = []
            for d in sorted(by_date.keys()):
                day_str = d.strftime("%Y-%m-%d")
                items = by_date[d][:max_headlines_per_day]
                parts = [f"{h.strip()} [{u}]" for h, u in items if h or u]
                lines.append(day_str + ": " + " | ".join(parts))
            period_data = "\n".join(lines)

            return run_article_agent(
                target_date=target_date,
                days_before=days_before,
                max_headlines_per_day=max_headlines_per_day,
                period_data=period_data,
            )
        finally:
            if session:
                session.close()
