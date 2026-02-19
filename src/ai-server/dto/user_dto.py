from pydantic import BaseModel, Field, EmailStr, validator, ConfigDict
from typing import Optional, List, Annotated
from enum import Enum
from datetime import datetime
from typing import Any
from fastapi import Depends
from dto.exchange_credentials_dto import ExchangeProvider


class SignupType(int, Enum):
    LOCAL = 0  # 로컬 가입
    SNS = 1  # SNS 가입


class SnsProvider(int, Enum):
    NAVER = 1  # 네이버
    KAKAO = 2  # 카카오
    GOOGLE = 3  # 구글
    APPLE = 4  # 애플


class SignupRequest(BaseModel):
    """회원가입 요청 DTO - Users 모델 기반"""

    email: EmailStr = Field(..., description="이메일 주소 (unique)")
    nickname: str = Field(
        ..., min_length=1, max_length=20, description="닉네임 (unique)"
    )
    signup_type: SignupType = Field(..., description="가입 타입 (0: 로컬, 1: SNS)")

    # 로컬 가입시에만 필요한 필드
    password: Optional[str] = Field(
        None, min_length=8, description="비밀번호 (해시화되어 저장)"
    )

    # SNS 가입시에만 필요한 필드
    sns_provider: Optional[SnsProvider] = Field(
        None, description="SNS 제공자 (1:naver, 2:kakao, 3:google, 4:apple)"
    )
    sns_id: Optional[str] = Field(
        None, max_length=255, description="SNS 제공자 고유 식별자"
    )

    @validator("password")
    def validate_password(cls, v, values):
        """로컬 가입시 비밀번호 필수"""
        if values.get("signup_type") == SignupType.LOCAL and not v:
            raise ValueError("로컬 가입시 비밀번호는 필수입니다.")
        return v

    @validator("sns_provider", "sns_id")
    def validate_sns_fields(cls, v, values):
        """SNS 가입시 SNS 정보 필수"""
        if values.get("signup_type") == SignupType.SNS:
            if not values.get("sns_provider") or not values.get("sns_id"):
                raise ValueError("SNS 가입시 SNS 제공자와 ID는 필수입니다.")
        return v

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "email": "user1@example.com",
                "nickname": "user1",
                "signup_type": 0,
                "password": "12345678",
                "sns_provider": None,
                "sns_id": None,
            }
        }
    )


class SignupResponse(BaseModel):
    """회원가입 응답 DTO - Users 모델 기반"""

    user_id: str = Field(..., description="사용자 UUID")
    email: str = Field(..., description="이메일 주소")
    nickname: str = Field(..., description="닉네임")
    signup_type: SignupType = Field(..., description="가입 타입")
    created_at: str = Field(..., description="가입 시간")
    is_active: bool = Field(True, description="활성 상태")
    is_connect_exchange: bool = Field(False, description="거래소 연결 여부")
    connected_exchanges: Optional[List[str]] = Field(
        None, description="연결된 거래소 목록"
    )

    @classmethod
    def from_user(cls, user):
        """User 모델에서 SignupResponse 생성"""
        return cls(
            user_id=str(user.id),
            email=str(user.email),
            nickname=str(user.nickname),
            signup_type=SignupType(user.signup_type),
            created_at=(
                user.created_at.isoformat()
                if user.created_at
                else "2024-01-01T00:00:00"
            ),
            is_active=bool(user.is_active),
            is_connect_exchange=bool(user.is_connect_exchange),
            connected_exchanges=user.connected_exchanges or [],
        )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "user_id": "123e4567-e89b-12d3-a456-426614174000",
                "email": "user@example.com",
                "nickname": "testuser",
                "signup_type": 0,
                "created_at": "2024-01-01T00:00:00",
                "is_active": True,
                "is_connect_exchange": False,
                "connected_exchanges": [],
            }
        }
    )


class LoginRequest(BaseModel):
    """로그인 요청 DTO"""

    email: EmailStr = Field(..., description="이메일 주소")
    password: str = Field(..., min_length=1, description="비밀번호")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {"email": "user1@example.com", "password": "12345678"}
        }
    )


class LoginResponse(BaseModel):
    """로그인 응답 DTO"""

    user_id: str = Field(..., description="사용자 UUID")
    email: str = Field(..., description="이메일 주소")
    nickname: str = Field(..., description="닉네임")
    signup_type: SignupType = Field(..., description="가입 타입")
    is_active: bool = Field(..., description="활성 상태")
    is_connect_exchange: bool = Field(..., description="거래소 연결 여부")
    connected_exchanges: Optional[List[str]] = Field(
        None, description="연결된 거래소 목록"
    )
    last_login_at: Optional[str] = Field(None, description="마지막 로그인 시간")
    access_token: str = Field(..., description="액세스 토큰")
    token_type: str = Field("bearer", description="토큰 타입")

    @classmethod
    def from_user(cls, user, access_token: str = "dummy_token"):
        """User 모델에서 LoginResponse 생성"""
        return cls(
            user_id=str(user.id),
            email=str(user.email),
            nickname=str(user.nickname),
            signup_type=SignupType(user.signup_type),
            is_active=bool(user.is_active),
            is_connect_exchange=bool(user.is_connect_exchange),
            connected_exchanges=user.connected_exchanges or [],
            last_login_at=(
                user.last_login_at.isoformat() if user.last_login_at else None
            ),
            access_token=access_token,
            token_type="bearer",
        )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "user_id": "123e4567-e89b-12d3-a456-426614174000",
                "email": "user@example.com",
                "nickname": "testuser",
                "signup_type": 0,
                "is_active": True,
                "is_connect_exchange": False,
                "connected_exchanges": [],
                "last_login_at": "2024-01-01T00:00:00",
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "bearer",
            }
        }
    )


class UserProfileResponse(BaseModel):
    """사용자 프로필 응답 DTO - Users 모델 기반"""

    user_id: str = Field(..., description="사용자 UUID")
    email: str = Field(..., description="이메일 주소")
    nickname: str = Field(..., description="닉네임")
    signup_type: SignupType = Field(..., description="가입 타입")
    sns_provider: Optional[SnsProvider] = Field(None, description="SNS 제공자")
    created_at: str = Field(..., description="가입 시간")
    last_login_at: Optional[str] = Field(None, description="마지막 로그인 시간")
    last_trading_history_update_at: Optional[str] = Field(
        None, description="거래내역 마지막 업데이트"
    )
    is_active: bool = Field(..., description="활성 상태")
    is_connect_exchange: bool = Field(..., description="거래소 연결 여부")
    connected_exchanges: Optional[List[str]] = Field(
        None, description="연결된 거래소 목록"
    )

    @classmethod
    def from_user(cls, user):
        """User 모델에서 UserProfileResponse 생성"""
        return cls(
            user_id=str(user.id),
            email=str(user.email),
            nickname=str(user.nickname),
            signup_type=SignupType(user.signup_type),
            sns_provider=SnsProvider(user.sns_provider) if user.sns_provider else None,
            created_at=(
                user.created_at.isoformat()
                if user.created_at
                else "2024-01-01T00:00:00"
            ),
            last_login_at=(
                user.last_login_at.isoformat() if user.last_login_at else None
            ),
            last_trading_history_update_at=(
                user.last_trading_history_update_at.isoformat()
                if user.last_trading_history_update_at
                else None
            ),
            is_active=bool(user.is_active),
            is_connect_exchange=bool(user.is_connect_exchange),
            connected_exchanges=user.connected_exchanges or [],
        )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "user_id": "123e4567-e89b-12d3-a456-426614174000",
                "email": "user@example.com",
                "nickname": "testuser",
                "signup_type": 0,
                "sns_provider": None,
                "created_at": "2024-01-01T00:00:00",
                "last_login_at": "2024-01-01T00:00:00",
                "last_trading_history_update_at": None,
                "is_active": True,
                "is_connect_exchange": False,
                "connected_exchanges": [],
            }
        }
    )


class UpdateTradingHistoryRequest(BaseModel):
    """거래내역 업데이트 요청 DTO"""

    user_id: str = Field(default="", description="사용자 UUID")
    exchange_provider_str: str = Field(
        ..., description="거래소 제공자 (UPBIT, BITHUMB, BINANCE, OKX)"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "user_id": "e953a0e1-5466-40b3-9207-cd86b7d95275",
                "exchange_provider_str": "UPBIT",
            }
        }
    )
