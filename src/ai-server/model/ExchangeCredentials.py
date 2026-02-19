from sqlalchemy import Column, String, Text, TIMESTAMP, func, ForeignKey, SmallInteger
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from database.database_connection import db
from enum import Enum


class ExchangeProvider(int, Enum):

    UPBIT = 1  # 업비트
    BITHUMB = 2  # 빗썸
    BINANCE = 3  # 바이낸스
    OKX = 4  # OKX


class ExchangeCredentials(db.Base):
    __tablename__ = "exchange_credentials"

    # users의 uuid와 동일한 값을 가짐. users 삭제시, 삭제. 이것도 pk 임
    user_id = Column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )

    exchange_provider = Column(
        SmallInteger, nullable=False
    )  # 1: 업비트, 2:빗썸, 3:바이낸스, 4:OKX

    encrypted_access_key = Column(Text, nullable=False)  # 암호화 하여 저장
    encrypted_secret_key = Column(Text, nullable=False)  # 암호화 하여 저장

    created_at = Column(TIMESTAMP, default=func.now())
    last_updated_at = Column(TIMESTAMP)

    # 관계 설정
    user = relationship("Users", back_populates="exchange_credentials")

    def __repr__(self):
        return f"<ExchangeCredentials(user_id={self.user_id}, provider={self.exchange_provider})>"

    @property
    def provider_name(self) -> str:
        """거래소 제공자 이름 반환"""
        try:
            return ExchangeProvider(self.exchange_provider).name
        except ValueError:
            return f"Unknown({self.exchange_provider})"

    def update_timestamp(self):
        """마지막 업데이트 시간 갱신"""
        from datetime import datetime

        self.last_updated_at = datetime.now()
