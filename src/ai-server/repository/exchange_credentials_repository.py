import logging
from typing import Optional
from database.database_connection import db
from model.ExchangeCredentials import ExchangeCredentials, ExchangeProvider
from utils.encryption import get_encryption_manager


class ExchangeCredentialsRepository:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.encryption_manager = get_encryption_manager()

    def save_credentials(self, credentials: ExchangeCredentials) -> ExchangeCredentials:
        """거래소 자격증명 저장/업데이트"""
        try:
            session = db.get_session()

            # 기존 자격증명이 있는지 확인
            existing = (
                session.query(ExchangeCredentials)
                .filter(
                    ExchangeCredentials.user_id == credentials.user_id,
                    ExchangeCredentials.exchange_provider
                    == credentials.exchange_provider,
                )
                .first()
            )

            if existing:
                # 기존 자격증명 업데이트
                existing.encrypted_access_key = credentials.encrypted_access_key
                existing.encrypted_secret_key = credentials.encrypted_secret_key
                existing.update_timestamp()
                session.commit()
                session.refresh(existing)

                self.logger.info(
                    f"거래소 자격증명 업데이트 완료: user_id={credentials.user_id}, provider={credentials.exchange_provider}"
                )
                return existing
            else:
                # 새로운 자격증명 저장
                session.add(credentials)
                session.commit()
                session.refresh(credentials)

                self.logger.info(
                    f"거래소 자격증명 저장 완료: user_id={credentials.user_id}, provider={credentials.exchange_provider}"
                )
                return credentials

        except Exception as e:
            self.logger.error(f"거래소 자격증명 저장 중 에러 발생: {e}")
            session.rollback()
            raise e
        finally:
            session.close()

    def find_by_user_and_provider(
        self, user_id: str, exchange_provider: ExchangeProvider
    ) -> Optional[ExchangeCredentials]:
        """사용자 ID와 거래소 제공자로 자격증명 조회"""
        try:
            session = db.get_session()
            credentials = (
                session.query(ExchangeCredentials)
                .filter(
                    ExchangeCredentials.user_id == user_id,
                    ExchangeCredentials.exchange_provider == exchange_provider,
                )
                .first()
            )
            return credentials
        except Exception as e:
            self.logger.error(f"거래소 자격증명 조회 중 에러 발생: {e}")
            raise e
        finally:
            session.close()

    def find_by_user_id(self, user_id: str) -> list[ExchangeCredentials]:
        """사용자 ID로 모든 거래소 자격증명 조회"""
        try:
            session = db.get_session()
            credentials = (
                session.query(ExchangeCredentials)
                .filter(ExchangeCredentials.user_id == user_id)
                .all()
            )
            return credentials
        except Exception as e:
            self.logger.error(f"사용자 거래소 자격증명 조회 중 에러 발생: {e}")
            raise e
        finally:
            session.close()

    def delete_credentials(
        self, user_id: str, exchange_provider: ExchangeProvider
    ) -> bool:
        """거래소 자격증명 삭제"""
        try:
            session = db.get_session()
            credentials = (
                session.query(ExchangeCredentials)
                .filter(
                    ExchangeCredentials.user_id == user_id,
                    ExchangeCredentials.exchange_provider == exchange_provider,
                )
                .first()
            )

            if credentials:
                session.delete(credentials)
                session.commit()

                self.logger.info(
                    f"거래소 자격증명 삭제 완료: user_id={user_id}, provider={exchange_provider}"
                )
                return True
            else:
                self.logger.warning(
                    f"삭제할 거래소 자격증명이 없습니다: user_id={user_id}, provider={exchange_provider}"
                )
                return False

        except Exception as e:
            self.logger.error(f"거래소 자격증명 삭제 중 에러 발생: {e}")
            session.rollback()
            raise e
        finally:
            session.close()

    def encrypt_key(self, key: str) -> str:
        """키 암호화"""
        return self.encryption_manager.encrypt(key)

    def decrypt_key(self, encrypted_key: str) -> str:
        """키 복호화"""
        return self.encryption_manager.decrypt(encrypted_key)
