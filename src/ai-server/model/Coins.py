from sqlalchemy import Column, String, Boolean, Integer, TIMESTAMP, func
from sqlalchemy.orm import relationship
from database.database_connection import db


class Coins(db.Base):
    __tablename__ = "coins"

    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String(20), nullable=False)  # BTC, ETH
    quote_currency = Column(String(10), nullable=False)  # KRW, BTC, USDT
    market_code = Column(String(20), unique=True)  # BTC/KRW
    korean_name = Column(String(50))
    english_name = Column(String(50))
    img_url = Column(String(1000))
    exchange = Column(String(20), nullable=False, default="upbit")  # 거래소 식별자
    is_active = Column(Boolean, default=True)

    # 관계 설정
    trading_histories = relationship("TradingHistories", back_populates="coin")
    assets = relationship("Assets", back_populates="coin")
    coin_holdings_past = relationship("CoinHoldingsPast", back_populates="coin")
    coin_prices_day = relationship("CoinPricesDay", back_populates="coin")

    def __repr__(self):
        return f"<Coin(id={self.id}, symbol={self.symbol}, market_code={self.market_code})>"
