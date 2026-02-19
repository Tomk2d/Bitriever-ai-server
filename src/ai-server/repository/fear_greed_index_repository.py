import logging
from datetime import date
from typing import List, Tuple

from database.database_connection import db
from model.FearGreedIndex import FearGreedIndex


class FearGreedIndexRepository:
    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def find_by_date_range(
        self, session, start_date: date, end_date: date
    ) -> List[Tuple[date, int]]:
        """해당 구간의 (date, value) 리스트를 date 오름차순으로 반환."""
        q = (
            session.query(FearGreedIndex.date, FearGreedIndex.value)
            .filter(
                FearGreedIndex.date >= start_date,
                FearGreedIndex.date <= end_date,
            )
            .order_by(FearGreedIndex.date.asc())
        )
        return [(row.date, row.value) for row in q.all()]
