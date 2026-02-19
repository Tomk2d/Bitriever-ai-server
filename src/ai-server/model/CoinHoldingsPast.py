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


class CoinHoldingsPast(db.Base):
    __tablename__ = "coin_holdings_past"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    coin_id = Column(Integer, ForeignKey("coins.id", ondelete="SET NULL"), nullable=True)
    exchange_code = Column(SmallInteger, nullable=False)  # 1:Upbit, 2:Bithumb, 3:Binance, 4:OKX
    symbol = Column(String(20), nullable=False)
    avg_buy_price = Column(Numeric(20, 8), nullable=False, default=0)
    remaining_quantity = Column(Numeric(20, 8), nullable=False, default=0)
    created_at = Column(TIMESTAMP, default=func.now())
    updated_at = Column(TIMESTAMP, default=func.now(), onupdate=func.now())

    # Relationships
    user = relationship("Users", back_populates="coin_holdings_past")
    coin = relationship("Coins", back_populates="coin_holdings_past")

    # Constraints
    __table_args__ = (
        UniqueConstraint(
            "user_id", "coin_id", "exchange_code", name="uk_coin_holdings_past_user_coin_exchange"
        ),
        CheckConstraint("exchange_code IN (1, 2, 3, 4)", name="chk_exchange_code_valid"),
        CheckConstraint("remaining_quantity >= 0", name="chk_remaining_quantity_non_negative"),
        CheckConstraint("avg_buy_price >= 0", name="chk_avg_buy_price_non_negative"),
    )

    def __repr__(self):
        return f"<CoinHoldingsPast(id={self.id}, user_id={self.user_id}, coin_id={self.coin_id}, symbol={self.symbol}, remaining_quantity={self.remaining_quantity})>"

