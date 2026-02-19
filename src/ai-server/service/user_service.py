import logging
from typing import Dict, Any
from model.Users import Users
from dto.user_dto import SignupRequest, SignupResponse, LoginResponse
import bcrypt
from datetime import datetime
import pytz
from utils.time_utils import get_current_korea_time


class UserService:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self._user_repository = None

    @property
    def user_repository(self):
        if self._user_repository is None:
            from dependencies import get_user_repository

            self._user_repository = get_user_repository()
        return self._user_repository

    def signup(self, user_data: SignupRequest) -> SignupResponse:
        try:
            if not user_data.password or user_data.password.strip() == "":
                raise ValueError("비밀번호는 필수입니다.")

            hashed_password = self._hash_password(user_data.password)

            user = Users(
                email=user_data.email,
                nickname=user_data.nickname,
                password_hash=hashed_password,
                signup_type=user_data.signup_type,
                sns_provider=user_data.sns_provider,
                sns_id=user_data.sns_id,
            )

            saved_user = self.user_repository.save_user(user)
            return SignupResponse.from_user(saved_user)

        except ValueError as e:
            raise e
        except Exception as e:
            raise e

    def login(self, email: str, password: str) -> LoginResponse:
        try:
            user = self.user_repository.find_by_email(email)
            if not user:
                raise ValueError("존재하지 않는 이메일입니다.")

            if not self._verify_password(password, str(user.password_hash)):
                raise ValueError("비밀번호가 일치하지 않습니다.")

            return LoginResponse.from_user(user)

        except ValueError as e:
            raise e
        except Exception as e:
            raise e

    def check_email_duplicate(self, email: str) -> bool:
        try:
            existing_user = self.user_repository.find_by_email(email)
            is_duplicate = existing_user is not None

            return is_duplicate

        except Exception as e:
            raise e

    def check_nickname_duplicate(self, nickname: str) -> bool:
        try:
            existing_user = self.user_repository.find_by_nickname(nickname)
            is_duplicate = existing_user is not None

            return is_duplicate

        except Exception as e:
            raise e

    def _hash_password(self, password: str) -> str:
        return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

    def _verify_password(self, plain_password: str, hashed_password: str) -> bool:
        return bcrypt.checkpw(
            plain_password.encode("utf-8"), hashed_password.encode("utf-8")
        )

    def update_user_trading_history_updated_at(self, user_id: str):
        try:
            user = self.user_repository.find_by_id(user_id)
            if user:
                user.last_trading_history_update_at = get_current_korea_time()
                self.user_repository.save_user(user)
                self.logger.info(f"사용자 거래내역 업데이트 시간 갱신: user_id={user_id}")
            else:
                self.logger.warning(f"사용자를 찾을 수 없습니다: user_id={user_id}")
        except Exception as e:
            self.logger.error(f"사용자 거래내역 업데이트 시간 갱신 실패: user_id={user_id}, error={e}")
            raise e
