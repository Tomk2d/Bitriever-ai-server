import logging
from typing import Optional

from database.database_connection import db
from model.Diary import Diary


class DiaryRepository:
    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def find_by_trading_history_id(self, session, trading_history_id: int) -> Optional[Diary]:
        """trading_history_id로 매매 일지 1건 조회. 없으면 None."""
        return (
            session.query(Diary)
            .filter(Diary.trading_history_id == trading_history_id)
            .first()
        )
