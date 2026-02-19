import logging
from typing import Optional, List
from model.ExchangeCredentials import (
    ExchangeCredentials,
    ExchangeProvider as ModelExchangeProvider,
)
from dto.exchange_credentials_dto import (
    ExchangeCredentialsRequest,
    ExchangeCredentialsResponse,
    ExchangeProvider as DTOExchangeProvider,
)


class ExchangeCredentialsService:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self._credentials_repository = None
        self._user_repository = None

    @property
    def credentials_repository(self):
        if self._credentials_repository is None:
            from repository.exchange_credentials_repository import (
                ExchangeCredentialsRepository,
            )

            self._credentials_repository = ExchangeCredentialsRepository()
        return self._credentials_repository

    @property
    def user_repository(self):
        if self._user_repository is None:
            from dependencies import get_user_repository

            self._user_repository = get_user_repository()
        return self._user_repository

    def save_credentials(
        self, user_id: str, request: ExchangeCredentialsRequest
    ) -> ExchangeCredentialsResponse:
        """거래소 자격증명 저장/업데이트"""
        try:
            # 사용자 존재 확인
            user = self.user_repository.find_by_id(user_id)
            if not user:
                raise ValueError("사용자를 찾을 수 없습니다.")

            # 키 암호화
            encrypted_access_key = self.credentials_repository.encrypt_key(
                request.access_key
            )
            encrypted_secret_key = self.credentials_repository.encrypt_key(
                request.secret_key
            )

            # 자격증명 모델 생성
            credentials = ExchangeCredentials(
                user_id=user_id,
                exchange_provider=request.exchange_provider,
                encrypted_access_key=encrypted_access_key,
                encrypted_secret_key=encrypted_secret_key,
            )

            # 저장
            saved_credentials = self.credentials_repository.save_credentials(
                credentials
            )

            # 사용자의 connected_exchanges 업데이트
            provider_name = DTOExchangeProvider(request.exchange_provider).name

            # Users 테이블 업데이트 - 타입 안전하게 처리
            current_exchanges = user.connected_exchanges or []

            # 이미 연결된 거래소인지 확인
            if provider_name not in current_exchanges:
                current_exchanges.append(provider_name)

            # SQLAlchemy 모델에 값 할당 (실제 값 타입 사용)
            setattr(user, "connected_exchanges", current_exchanges)
            setattr(user, "is_connect_exchange", True)

            # Users 테이블 저장
            self.user_repository.save_user(user)

            self.logger.info(
                f"사용자 {user_id}의 {provider_name} 연결 정보 업데이트 완료"
            )

            return ExchangeCredentialsResponse.from_credentials(saved_credentials)

        except Exception as e:
            self.logger.error(f"거래소 자격증명 저장 실패: {e}")
            raise

    def get_credentials(
        self, user_id: str, exchange_provider: DTOExchangeProvider
    ) -> Optional[ExchangeCredentialsResponse]:
        """거래소 자격증명 조회 (복호화된 키 포함)"""
        try:
            # DTO ExchangeProvider를 Model ExchangeProvider로 변환
            model_provider = ModelExchangeProvider(exchange_provider)

            credentials = self.credentials_repository.find_by_user_and_provider(
                user_id, model_provider
            )
            if not credentials:
                return None

            # 복호화된 키를 포함한 응답 생성
            decrypted_access_key = self.credentials_repository.decrypt_key(
                str(credentials.encrypted_access_key)  # str() 변환 추가
            )
            decrypted_secret_key = self.credentials_repository.decrypt_key(
                str(credentials.encrypted_secret_key)  # str() 변환 추가
            )

            return ExchangeCredentialsResponse(
                user_id=str(credentials.user_id),
                exchange_provider=DTOExchangeProvider(credentials.exchange_provider),
                provider_name=credentials.provider_name,
                created_at=(
                    credentials.created_at.isoformat()
                    if credentials.created_at is not None  # None 체크 수정
                    else "2024-01-01T00:00:00"
                ),
                last_updated_at=(
                    credentials.last_updated_at.isoformat()
                    if credentials.last_updated_at is not None  # None 체크 수정
                    else None
                ),
                access_key=decrypted_access_key,  # 복호화된 키
                secret_key=decrypted_secret_key,  # 복호화된 키
            )

        except Exception as e:
            self.logger.error(f"거래소 자격증명 조회 실패: {e}")
            raise

    def get_all_credentials(self, user_id: str) -> List[ExchangeCredentialsResponse]:
        """사용자의 모든 거래소 자격증명 조회"""
        try:
            credentials_list = self.credentials_repository.find_by_user_id(user_id)
            responses = []

            for credentials in credentials_list:
                response = ExchangeCredentialsResponse.from_credentials(credentials)
                responses.append(response)

            return responses

        except Exception as e:
            self.logger.error(f"사용자 거래소 자격증명 조회 실패: {e}")
            raise

    def delete_credentials(
        self, user_id: str, exchange_provider: DTOExchangeProvider
    ) -> bool:
        """거래소 자격증명 삭제"""
        try:
            model_provider = ModelExchangeProvider(exchange_provider)

            success = self.credentials_repository.delete_credentials(
                user_id, model_provider
            )

            if success:
                user = self.user_repository.find_by_id(user_id)
                if user:
                    provider_name = DTOExchangeProvider(exchange_provider).name
                    current_exchanges = user.connected_exchanges or []

                    if provider_name in current_exchanges:
                        current_exchanges.remove(provider_name)

                    if (
                        isinstance(current_exchanges, list)
                        and len(current_exchanges) == 0
                    ):
                        setattr(user, "is_connect_exchange", False)

                    setattr(user, "connected_exchanges", current_exchanges)
                    self.user_repository.save_user(user)

            return success

        except Exception as e:
            self.logger.error(f"거래소 자격증명 삭제 실패: {e}")
            raise

    def verify_credentials(
        self, user_id: str, exchange_provider: DTOExchangeProvider
    ) -> bool:
        """거래소 자격증명 유효성 검증"""
        try:
            # DTO ExchangeProvider를 Model ExchangeProvider로 변환
            model_provider = ModelExchangeProvider(exchange_provider)

            credentials = self.credentials_repository.find_by_user_and_provider(
                user_id, model_provider
            )
            if not credentials:
                return False

            # 복호화 테스트
            try:
                self.credentials_repository.decrypt_key(
                    str(credentials.encrypted_access_key)  # str() 변환 추가
                )
                self.credentials_repository.decrypt_key(
                    str(credentials.encrypted_secret_key)  # str() 변환 추가
                )
                return True
            except Exception:
                return False

        except Exception as e:
            self.logger.error(f"거래소 자격증명 검증 실패: {e}")
            return False
