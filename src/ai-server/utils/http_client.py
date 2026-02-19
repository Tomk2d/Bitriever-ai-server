import requests
import time
import os
from typing import Optional, Dict, Any
import logging


class Http_client:
    def __init__(self, base_url: str, headers: Optional[dict] = None):
        self.base_url = base_url
        self.headers = (
            headers
            if headers is not None
            else {
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept": "application/json, text/plain, */*",
                "Accept-Language": "ko-KR,ko;q=0.9,en;q=0.8",
                "Accept-Encoding": "gzip, deflate, br",
                "Connection": "keep-alive",
                "Sec-Fetch-Dest": "empty",
                "Sec-Fetch-Mode": "cors",
                "Sec-Fetch-Site": "cross-site",
            }
        )
        self.logger = logging.getLogger(__name__)

    def get(self, params: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        try:
            response = requests.get(
                self.base_url, headers=self.headers, params=params, timeout=30
            )

            response.raise_for_status()

            # Content-Type 확인
            content_type = response.headers.get("content-type", "")
            if "application/json" not in content_type:
                self.logger.warning(f"예상하지 못한 Content-Type: {content_type}")

            return response.json()

        except requests.exceptions.RequestException as e:
            self.logger.error(f"HTTP 요청 에러: {e}")
            if hasattr(e, "response") and e.response is not None:
                self.logger.error(f"응답 상태 코드: {e.response.status_code}")
                self.logger.error(f"응답 내용: {e.response.text}")
            return None
        except ValueError as e:
            self.logger.error(f"JSON 파싱 에러: {e}")
            self.logger.error(f"응답 내용: {response.text[:500]}...")
            return None
        except Exception as e:
            self.logger.error(f"예상치 못한 에러: {e}")
            return None

    def get_with_nonce(self) -> Optional[Dict[str, Any]]:
        """
        nonce 파라미터를 포함하여 요청을 보냅니다.
        """
        nonce = int(time.time() * 1000)  # 현재 시간을 밀리초로
        params = {"nonce": nonce}
        return self.get(params)

    def download_image(self, url: str, save_path: str) -> bool:
        try:
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            response = requests.get(url, headers=self.headers, timeout=30)
            response.raise_for_status()
            with open(save_path, "wb") as f:
                f.write(response.content)
            self.logger.info(f"이미지 저장 성공: {save_path}")
            return True
        except Exception as e:
            self.logger.error(f"이미지 다운로드 실패: {e}")
            return False
