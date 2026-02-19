from sqlalchemy import (
    Column,
    String,
    Integer,
    Numeric,
    TIMESTAMP,
    BigInteger,
    ForeignKey,
    func,
)
from sqlalchemy.orm import relationship
from database.database_connection import db


class CoinPricesDay(db.Base):
    __tablename__ = "coin_prices_day"

    id = Column(Integer, primary_key=True, autoincrement=True)
    coin_id = Column(
        Integer, ForeignKey("coins.id", ondelete="CASCADE"), nullable=False
    )
    market_code = Column(String(20), nullable=False)
    candle_date_time_utc = Column(TIMESTAMP, nullable=False)
    candle_date_time_kst = Column(TIMESTAMP, nullable=False)
    opening_price = Column(Numeric(20, 8), nullable=False)
    high_price = Column(Numeric(20, 8), nullable=False)
    low_price = Column(Numeric(20, 8), nullable=False)
    trade_price = Column(Numeric(20, 8), nullable=False)
    timestamp = Column(BigInteger, nullable=False)
    candle_acc_trade_price = Column(Numeric(30, 8), nullable=False)
    candle_acc_trade_volume = Column(Numeric(30, 8), nullable=False)
    prev_closing_price = Column(Numeric(20, 8), nullable=False)
    change_price = Column(Numeric(20, 8), nullable=False)
    change_rate = Column(Numeric(20, 8), nullable=False)
    converted_trade_price = Column(Numeric(20, 8), nullable=True)
    created_at = Column(TIMESTAMP, default=func.now())
    updated_at = Column(TIMESTAMP, default=func.now(), onupdate=func.now())

    # 관계 설정
    coin = relationship("Coins", back_populates="coin_prices_day")

    def __repr__(self):
        return f"<CoinPricesDay(id={self.id}, coin_id={self.coin_id}, market_code={self.market_code}, date={self.candle_date_time_utc})>"

