import os
import base64
import logging
from typing import Optional
from cryptography.fernet import Fernet

# 사용하지 않는 import 제거
# from cryptography.hazmat.primitives import hashes
# from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC


class EncryptionManager:
    """암호화/복호화 관리자"""

    def __init__(self, secret_key: Optional[str] = None):
        self.logger = logging.getLogger(__name__)
        self._secret_key = secret_key
        self._fernet: Optional[Fernet] = None

        if secret_key:
            self._initialize_fernet()

    def _initialize_fernet(self):
        """Fernet 인스턴스 초기화"""
        try:
            # 시크릿 키를 바이트로 변환
            if isinstance(self._secret_key, str):
                key_bytes = self._secret_key.encode("utf-8")
            elif isinstance(self._secret_key, bytes):
                key_bytes = self._secret_key
            else:
                raise ValueError("시크릿 키는 문자열 또는 바이트여야 합니다.")

            # 32바이트 키로 패딩 (Fernet 요구사항)
            if len(key_bytes) < 32:
                # 부족한 경우 패딩
                key_bytes = key_bytes.ljust(32, b"\0")
            elif len(key_bytes) > 32:
                # 긴 경우 잘라내기
                key_bytes = key_bytes[:32]

            # base64 인코딩 (Fernet 요구사항)
            key_b64 = base64.urlsafe_b64encode(key_bytes)
            self._fernet = Fernet(key_b64)

            self.logger.info("Fernet 암호화 인스턴스 초기화 완료")

        except Exception as e:
            self.logger.error(f"Fernet 초기화 실패: {e}")
            raise

    def set_secret_key(self, secret_key: str):
        """시크릿 키 설정"""
        self._secret_key = secret_key
        self._initialize_fernet()

    def encrypt(self, data: str) -> str:
        """데이터 암호화"""
        if not self._fernet:
            raise ValueError("시크릿 키가 설정되지 않았습니다.")

        try:
            encrypted_data = self._fernet.encrypt(data.encode("utf-8"))
            return base64.urlsafe_b64encode(encrypted_data).decode("utf-8")
        except Exception as e:
            self.logger.error(f"암호화 실패: {e}")
            raise

    def decrypt(self, encrypted_data: str) -> str:
        """데이터 복호화"""
        if not self._fernet:
            raise ValueError("시크릿 키가 설정되지 않았습니다.")

        try:
            # base64 디코딩
            encrypted_bytes = base64.urlsafe_b64decode(encrypted_data.encode("utf-8"))
            decrypted_data = self._fernet.decrypt(encrypted_bytes)
            return decrypted_data.decode("utf-8")
        except Exception as e:
            self.logger.error(f"복호화 실패: {e}")
            raise

    def is_initialized(self) -> bool:
        """초기화 상태 확인"""
        return self._fernet is not None


# 싱글톤 인스턴스
_encryption_manager: Optional[EncryptionManager] = None


def get_encryption_manager() -> EncryptionManager:
    """암호화 관리자 싱글톤 인스턴스 반환"""
    global _encryption_manager
    if _encryption_manager is None:
        _encryption_manager = EncryptionManager()
    return _encryption_manager


def initialize_encryption_manager(secret_key: str):
    """암호화 관리자 초기화"""
    global _encryption_manager
    _encryption_manager = EncryptionManager(secret_key)
