import json
import logging
from typing import Optional
import boto3
from botocore.exceptions import ClientError, NoCredentialsError


class AWSSecretManager:
    """AWS Secret Manager 클라이언트"""

    def __init__(self, region_name: str = "ap-northeast-2"):
        self.logger = logging.getLogger(__name__)
        self.region_name = region_name
        self._client = None

    def _get_client(self):
        """boto3 클라이언트 생성"""
        if self._client is None:
            try:
                self._client = boto3.client(
                    "secretsmanager", region_name=self.region_name
                )
                self.logger.info(
                    f"AWS Secret Manager 클라이언트 생성 완료 (region: {self.region_name})"
                )
            except NoCredentialsError:
                self.logger.error("AWS 자격증명을 찾을 수 없습니다.")
                raise
            except Exception as e:
                self.logger.error(f"AWS Secret Manager 클라이언트 생성 실패: {e}")
                raise
        return self._client

    def get_secret(self, secret_name: str) -> str:
        """시크릿 값 조회"""
        try:
            client = self._get_client()
            response = client.get_secret_value(SecretId=secret_name)

            if "SecretString" in response:
                secret = response["SecretString"]
                self.logger.info(f"시크릿 조회 성공: {secret_name}")
                return secret
            else:
                # 바이너리 시크릿인 경우
                secret = response["SecretBinary"]
                self.logger.info(f"바이너리 시크릿 조회 성공: {secret_name}")
                return secret.decode("utf-8")

        except ClientError as e:
            error_code = e.response["Error"]["Code"]
            if error_code == "ResourceNotFoundException":
                self.logger.error(f"시크릿을 찾을 수 없습니다: {secret_name}")
                raise ValueError(f"시크릿을 찾을 수 없습니다: {secret_name}")
            elif error_code == "InvalidRequestException":
                self.logger.error(f"잘못된 요청입니다: {secret_name}")
                raise ValueError(f"잘못된 요청입니다: {secret_name}")
            elif error_code == "InvalidParameterException":
                self.logger.error(f"잘못된 파라미터입니다: {secret_name}")
                raise ValueError(f"잘못된 파라미터입니다: {secret_name}")
            else:
                self.logger.error(f"시크릿 조회 실패: {error_code}")
                raise
        except Exception as e:
            self.logger.error(f"시크릿 조회 중 예상치 못한 오류: {e}")
            raise

    def get_secret_as_json(self, secret_name: str) -> dict:
        """JSON 형태의 시크릿 값 조회"""
        secret_string = self.get_secret(secret_name)
        try:
            return json.loads(secret_string)
        except json.JSONDecodeError as e:
            self.logger.error(f"JSON 파싱 실패: {e}")
            raise ValueError(f"시크릿이 유효한 JSON 형식이 아닙니다: {secret_name}")

    def create_secret(
        self, secret_name: str, secret_value: str, description: str = ""
    ) -> bool:
        """새로운 시크릿 생성"""
        try:
            client = self._get_client()
            response = client.create_secret(
                Name=secret_name, SecretString=secret_value, Description=description
            )
            self.logger.info(f"시크릿 생성 성공: {secret_name}")
            return True
        except ClientError as e:
            error_code = e.response["Error"]["Code"]
            if error_code == "ResourceExistsException":
                self.logger.warning(f"시크릿이 이미 존재합니다: {secret_name}")
                return False
            else:
                self.logger.error(f"시크릿 생성 실패: {error_code}")
                raise
        except Exception as e:
            self.logger.error(f"시크릿 생성 중 예상치 못한 오류: {e}")
            raise

    def update_secret(self, secret_name: str, secret_value: str) -> bool:
        """시크릿 값 업데이트"""
        try:
            client = self._get_client()
            response = client.update_secret(
                SecretId=secret_name, SecretString=secret_value
            )
            self.logger.info(f"시크릿 업데이트 성공: {secret_name}")
            return True
        except ClientError as e:
            error_code = e.response["Error"]["Code"]
            if error_code == "ResourceNotFoundException":
                self.logger.error(
                    f"업데이트할 시크릿을 찾을 수 없습니다: {secret_name}"
                )
                raise ValueError(f"업데이트할 시크릿을 찾을 수 없습니다: {secret_name}")
            else:
                self.logger.error(f"시크릿 업데이트 실패: {error_code}")
                raise
        except Exception as e:
            self.logger.error(f"시크릿 업데이트 중 예상치 못한 오류: {e}")
            raise

    def delete_secret(self, secret_name: str, force_delete: bool = False) -> bool:
        """시크릿 삭제"""
        try:
            client = self._get_client()
            response = client.delete_secret(
                SecretId=secret_name, ForceDeleteWithoutRecovery=force_delete
            )
            self.logger.info(f"시크릿 삭제 성공: {secret_name}")
            return True
        except ClientError as e:
            error_code = e.response["Error"]["Code"]
            if error_code == "ResourceNotFoundException":
                self.logger.warning(f"삭제할 시크릿을 찾을 수 없습니다: {secret_name}")
                return False
            else:
                self.logger.error(f"시크릿 삭제 실패: {error_code}")
                raise
        except Exception as e:
            self.logger.error(f"시크릿 삭제 중 예상치 못한 오류: {e}")
            raise


# 싱글톤 인스턴스
_secret_manager: Optional[AWSSecretManager] = None


def get_secret_manager() -> AWSSecretManager:
    """AWS Secret Manager 싱글톤 인스턴스 반환"""
    global _secret_manager
    if _secret_manager is None:
        _secret_manager = AWSSecretManager()
    return _secret_manager
