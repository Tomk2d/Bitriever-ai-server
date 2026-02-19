import os
import logging
from utils.encryption import initialize_encryption_manager
from utils.aws_secret_manager import get_secret_manager
from dotenv import load_dotenv

logger = logging.getLogger(__name__)
load_dotenv()


def initialize_encryption():
    """암호화 시스템 초기화"""
    try:
        # AWS Secret Manager에서 암호화 키 가져오기
        secret_manager = get_secret_manager()

        # 환경변수에서 시크릿 이름 가져오기 (기본값: bit-diary-encryption-key)
        secret_name = os.getenv("ENCRYPTION_SECRET_NAME", "bit-diary-encryption-key")

        logger.info(f"🔐 암호화 키 조회 중: {secret_name}")
        encryption_key = secret_manager.get_secret(secret_name)

        # 암호화 관리자 초기화
        initialize_encryption_manager(encryption_key)
        logger.info("✅ 암호화 시스템 초기화 완료")

    except Exception as e:
        logger.error(f"❌ 암호화 시스템 초기화 실패: {e}")
        # 개발 환경에서는 .env에서 키 가져오기
        if os.getenv("ENVIRONMENT", "development") == "development":
            logger.warning("⚠️ 개발 환경에서 .env 파일의 암호화 키 사용")
            dev_key = os.getenv("DEV_ENCRYPTION_KEY")
            if not dev_key:
                logger.error("❌ DEV_ENCRYPTION_KEY가 .env 파일에 설정되지 않았습니다.")
                raise ValueError(
                    "개발 환경에서 DEV_ENCRYPTION_KEY 환경변수가 필요합니다."
                )

            initialize_encryption_manager(dev_key)
            logger.info("✅ 개발용 암호화 키로 초기화 완료")
        else:
            raise


def initialize_app():
    """애플리케이션 전체 초기화"""
    logger.info("🚀 애플리케이션 초기화 시작...")

    # 암호화 시스템 초기화
    initialize_encryption()

    logger.info("✅ 애플리케이션 초기화 완료")
