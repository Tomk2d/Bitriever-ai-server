from sqlalchemy import (
    Column,
    String,
    Integer,
    SmallInteger,
    Numeric,
    TIMESTAMP,
    func,
    ForeignKey,
    UniqueConstraint,
    CheckConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from database.database_connection import db


class TradingHistories(db.Base):
    __tablename__ = "trading_histories"

    id = Column(Integer, primary_key=True, autoincrement=True)  # 내부용 기본키

    user_id = Column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    coin_id = Column(
        Integer, ForeignKey("coins.id", ondelete="CASCADE"), nullable=False
    )

    exchange_code = Column(
        SmallInteger, nullable=False
    )  # 1:Upbit, 2:Bithumb, 3:Binance, 4:OKX
    trade_uuid = Column(String(100), nullable=False)  # 외부 체결 고유 ID

    trade_type = Column(SmallInteger, nullable=False)  # 0: 매수, 1: 매도

    price = Column(Numeric(20, 8), nullable=False)
    quantity = Column(Numeric(20, 8), nullable=False)
    total_price = Column(
        Numeric(20, 8), nullable=False
    )  # price * quantity (수동 계산 필요)

    fee = Column(Numeric(20, 8), default=0)  # 수수료
    trade_time = Column(TIMESTAMP, nullable=False)  # 체결시간
    created_at = Column(TIMESTAMP, default=func.now())  # 해당 칼럼 생성시간
    
    # 수익률 계산 관련 칼럼
    profit_loss_rate = Column(Numeric(5, 2), nullable=True)  # 상승하락률 (50% 상승 = 0.50, 50% 하락 = -0.50)
    avg_buy_price = Column(Numeric(20, 8), nullable=True)  # 구매 시 평균 단가

    # 관계 설정
    user = relationship("Users", back_populates="trading_histories")
    coin = relationship("Coins", back_populates="trading_histories")

    # 제약조건
    __table_args__ = (
        UniqueConstraint(
            "user_id", "exchange_code", "trade_uuid", name="uq_user_exchange_trade_uuid"
        ),
        CheckConstraint("exchange_code IN (1, 2, 3, 4)", name="chk_exchange_code"),
        CheckConstraint("trade_type IN (0, 1)", name="chk_trade_type"),
    )

    def __repr__(self):
        return f"<TradingHistory(id={self.id}, user_id={self.user_id}, trade_uuid={self.trade_uuid})>"
