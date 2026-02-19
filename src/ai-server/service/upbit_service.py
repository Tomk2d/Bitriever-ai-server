from dotenv import load_dotenv
from utils.upbit_http_client import UpbitHttpClient
import logging
from utils.time_utils import get_all_trading_time_ranges, get_current_korea_time
from datetime import datetime
import pytz
import time
from utils.http_client import Http_client
from typing import List, Dict, Any, Optional

load_dotenv()


class UpbitService:
    def __init__(self):
        self.upbit_http_client = UpbitHttpClient()
        self.logger = logging.getLogger(__name__)

    def fetch_all_trading_uuids(
        self, access_key: str, secret_key: str, start_time: Optional[datetime] = None
    ):
        try:
            # start_time이 None이면 기본값 사용
            if start_time is None:
                first_time = datetime(2017, 11, 1, tzinfo=pytz.timezone("Asia/Seoul"))
            else:
                # start_time이 타임존 정보가 없으면 한국 시간으로 설정
                if start_time.tzinfo is None:
                    first_time = pytz.timezone("Asia/Seoul").localize(start_time)
                else:
                    first_time = start_time

            current_time = get_current_korea_time()
            time_ranges = get_all_trading_time_ranges(first_time, current_time)

            all_uuids = []

            for i, (range_start, range_end) in enumerate(time_ranges):
                params = {
                    "states[]": ["done", "cancel"],
                    "start_time": range_start,
                    "end_time": range_end,
                    "limit": 1000,
                }

                response = self.upbit_http_client.get(
                    "/v1/orders/closed", access_key, secret_key, params, True
                )

                if response is None:
                    continue

                for r in response:
                    if isinstance(r, dict) and r.get("executed_volume") == "0":
                        continue

                    if isinstance(r, dict) and r.get("uuid"):
                        all_uuids.append(r.get("uuid"))

                if (i + 1) % 25 == 0:
                    time.sleep(1)

            return all_uuids
        except Exception as e:
            raise e

    def fetch_all_trading_history(self, access_key: str, secret_key: str, uuids: list):
        try:
            trading_histories = []

            time.sleep(1)
            for i, uuid in enumerate(uuids):
                if (i + 1) % 25 == 0:
                    time.sleep(1)

                params = {"uuid": uuid}
                response = self.upbit_http_client.get(
                    "/v1/order", access_key, secret_key, params, True
                )

                if response is None:
                    continue

                trading_histories.append(response)

            return trading_histories

        except Exception as e:
            raise e

    def fetch_all_coin_list(self) -> Any:
        try:
            base_url = "https://crix-static.upbit.com/crix_master"

            headers = {
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36",
                "Accept": "application/json, text/plain, */*",
                "Accept-Language": "ko-KR,ko;q=0.9,en;q=0.8",
                "Accept-Encoding": "gzip, deflate, br",
                "Origin": "https://upbit.com",
                "Referer": "https://upbit.com/",
                "Connection": "keep-alive",
                "Sec-Fetch-Dest": "empty",
                "Sec-Fetch-Mode": "cors",
                "Sec-Fetch-Site": "cross-site",
            }

            client = Http_client(base_url, headers)
            response = client.get_with_nonce()

            if response:
                # self.download_image(response, "https://static.upbit.com/logos/", "data/image/")

                return response
            else:
                self.logger.error("코인 목록 가져오기 실패")
                return None

        except Exception as e:
            self.logger.error(f"코인 목록 가져오기 중 에러 발생: {e}")
            raise e

    def download_image(self, coin_list: List[Dict[Any, Any]], url: str, save_path: str):
        try:
            client = Http_client(url)
            for i, r in enumerate(coin_list):
                if i % 5 == 0:
                    time.sleep(1)

                symbol = r.get("baseCurrencyCode")
                url = f"https://static.upbit.com/logos/{symbol}.png"
                client.download_image(url, f"../../data/image/{symbol}.png")
            self.logger.info(f"이미지 다운로드 완료: {len(coin_list)}개")
        except Exception as e:
            raise e

    def fetch_accounts(self, access_key: str, secret_key: str) -> List[Dict[str, Any]]:
        """Upbit 계정 잔고 조회"""
        try:
            response = self.upbit_http_client.get(
                "/v1/accounts", access_key, secret_key, None, True
            )

            if response is None:
                self.logger.warning("계정 잔고 조회 결과가 None입니다")
                return []

            return response if isinstance(response, list) else [response]

        except Exception as e:
            self.logger.error(f"계정 잔고 조회 중 에러 발생: {e}")
            raise e
