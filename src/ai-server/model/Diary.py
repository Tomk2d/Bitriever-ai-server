"""매매 일지. app-server와 동일한 diaries 테이블 참조 (trading_history_id로 1:1)."""

from sqlalchemy import Column, Integer, Text
from database.database_connection import db


class Diary(db.Base):
    __tablename__ = "diaries"

    id = Column(Integer, primary_key=True, autoincrement=True)
    trading_history_id = Column(Integer, nullable=False, unique=True)
    content = Column(Text)  # JSONB: {"blocks": [{"type": "text", "content": "..."}, ...]}
    trading_mind = Column(Integer, nullable=True)  # TradingMind code (0, 1, 2, 3, 11, 12, 13, 14)
