import logging
from datetime import datetime
from typing import List, Optional

from database.database_connection import db
from model.Article import Article


class ArticleRepository:
    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def find_by_published_at_between(
        self,
        session,
        start_dt: datetime,
        end_dt: datetime,
        publisher_type: Optional[int] = None,
    ) -> List[Article]:
        """published_at 구간 조회, published_at 내림차순(최신순). headline, published_at, original_url 사용."""
        q = (
            session.query(Article)
            .filter(
                Article.published_at >= start_dt,
                Article.published_at <= end_dt,
            )
            .order_by(Article.published_at.desc())
        )
        if publisher_type is not None:
            q = q.filter(Article.publisher_type == publisher_type)
        return q.all()
