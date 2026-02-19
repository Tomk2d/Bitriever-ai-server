from sqlalchemy import (
    Column,
    String,
    Integer,
    SmallInteger,
    Numeric,
    Boolean,
    TIMESTAMP,
    func,
    ForeignKey,
    UniqueConstraint,
    CheckConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from database.database_connection import db


class Assets(db.Base):
    __tablename__ = "assets"

    id = Column(Integer, primary_key=True, autoincrement=True)

    user_id = Column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    exchange_code = Column(SmallInteger, nullable=False)  # 1:Upbit, 2:Bithumb, 3:Binance, 4:OKX
    coin_id = Column(
        Integer, ForeignKey("coins.id", ondelete="SET NULL"), nullable=True
    )

    symbol = Column(String(20), nullable=False)  # BTC, ETH, KRW
    trade_by_symbol = Column(String(10), nullable=False)  # KRW, BTC, USDT

    quantity = Column(Numeric(20, 8), nullable=False, default=0)
    locked_quantity = Column(Numeric(20, 8), nullable=False, default=0)
    avg_buy_price = Column(Numeric(20, 8), nullable=False, default=0)
    avg_buy_price_modified = Column(Boolean, nullable=False, default=False)

    created_at = Column(TIMESTAMP, default=func.now())
    updated_at = Column(TIMESTAMP, default=func.now(), onupdate=func.now())

    # 관계 설정
    user = relationship("Users", back_populates="assets")
    coin = relationship("Coins", back_populates="assets")

    # 제약조건
    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "exchange_code",
            "symbol",
            "trade_by_symbol",
            name="uk_assets_user_exchange_symbol",
        ),
        CheckConstraint("exchange_code IN (1, 2, 3, 4)", name="chk_exchange_code"),
        CheckConstraint("quantity >= 0", name="chk_quantity_non_negative"),
        CheckConstraint("locked_quantity >= 0", name="chk_locked_quantity_non_negative"),
        CheckConstraint("avg_buy_price >= 0", name="chk_avg_buy_price_non_negative"),
    )

    def __repr__(self):
        return f"<Asset(id={self.id}, user_id={self.user_id}, symbol={self.symbol}, quantity={self.quantity})>"

