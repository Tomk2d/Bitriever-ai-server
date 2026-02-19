from sqlalchemy import Column, String, Text, TIMESTAMP, func, Boolean, SmallInteger
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from database.database_connection import db
import uuid
from typing import Optional, Dict, Any


class Users(db.Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    nickname = Column(String(20), unique=True, nullable=False, index=True)

    signup_type = Column(SmallInteger, nullable=False)  # 0: local, 1: sns
    password_hash = Column(Text)  # 로컬 가입자만 사용

    sns_provider = Column(SmallInteger)  # 1:naver, 2:kakao, 3:google, 4:apple
    sns_id = Column(String(255))  # SNS 제공자 고유 식별자

    created_at = Column(TIMESTAMP, default=func.now())
    last_login_at = Column(TIMESTAMP)
    last_trading_history_update_at = Column(TIMESTAMP)  # 거래내역 마지막 업데이트

    is_active = Column(Boolean, default=True)  # 휴면 계정, 탈퇴계정 여부
    is_connect_exchange = Column(
        Boolean, nullable=False, default=False
    )  # 거래소 연결 여부
    connected_exchanges = Column(JSONB, default=None)  # 연결된 거래소 목록

    # 관계 설정 - upbit_credentials를 exchange_credentials로 변경
    exchange_credentials = relationship(
        "ExchangeCredentials", back_populates="user", uselist=False
    )
    trading_histories = relationship("TradingHistories", back_populates="user")
    assets = relationship("Assets", back_populates="user")
    coin_holdings_past = relationship("CoinHoldingsPast", back_populates="user")

    def __repr__(self):
        return f"<User(id={self.id}, email={self.email}, nickname={self.nickname})>"
