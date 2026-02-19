"""매매 분석 결과. API 응답 data 전체를 JSONB로 저장."""

from sqlalchemy import Column, Integer, Date, TIMESTAMP, func, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from database.database_connection import db


class TradeEvaluationResult(db.Base):
    __tablename__ = "trade_evaluation_results"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    trade_id = Column(
        Integer,
        ForeignKey("trading_histories.id", ondelete="CASCADE"),
        nullable=False,
    )
    target_date = Column(Date, nullable=False)
    coin_id = Column(Integer, nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), default=func.now())
    result = Column(JSONB, nullable=False)

    def __repr__(self):
        return f"<TradeEvaluationResult(id={self.id}, trade_id={self.trade_id})>"
