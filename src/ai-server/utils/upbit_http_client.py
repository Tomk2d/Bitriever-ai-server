import requests
import hashlib
import jwt
import uuid
from urllib.parse import urlencode, unquote
from typing import Dict, Any, Optional, List


class UpbitHttpClientError(Exception):
    """Upbit HTTP Client 관련 에러"""

    pass


class UpbitHttpClient:
    def __init__(
        self,
        base_url: str = "https://api.upbit.com",
    ):
        self.base_url = base_url
        self.session = requests.Session()

    def _create_jwt_token(
        self, access_key: str, secret_key: str, params: Optional[Dict[str, Any]] = None
    ) -> str:
        """JWT 토큰 생성"""
        payload = {
            "access_key": access_key,
            "nonce": str(uuid.uuid4()),
        }

        if params:
            query_string = unquote(urlencode(params, doseq=True)).encode("utf-8")
            sha512 = hashlib.sha512()
            sha512.update(query_string)
            query_hash = sha512.hexdigest()

            payload.update(
                {
                    "query_hash": query_hash,
                    "query_hash_alg": "SHA512",
                }
            )

        return jwt.encode(payload, secret_key)

    def _get_headers(
        self, access_key: str, secret_key: str, params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, str]:
        """인증 헤더 생성"""
        jwt_token = self._create_jwt_token(access_key, secret_key, params)
        return {
            "Authorization": f"Bearer {jwt_token}",
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
        }

    def get(
        self,
        endpoint: str,
        access_key: str,
        secret_key: str,
        params: Optional[Dict[str, Any]] = None,
        require_auth: bool = False,  # 인증 헤더가 필요한지 체크
    ) -> Optional[Dict[str, Any]]:
        try:
            url = f"{self.base_url}{endpoint}"

            # 인증 헤더가 필요할때만 생성
            headers = (
                self._get_headers(access_key, secret_key, params)
                if require_auth
                else None
            )

            response = self.session.get(url, params=params, headers=headers)
            response.raise_for_status()

            return response.json()

        except requests.exceptions.RequestException as e:
            error_msg = (
                f"UpbitHttpClient GET request failed for endpoint {endpoint}: {e}"
            )
            raise UpbitHttpClientError(error_msg)
        except Exception as e:
            error_msg = f"UpbitHttpClient unexpected error in GET method for endpoint {endpoint}: {e}"
            raise UpbitHttpClientError(error_msg)
