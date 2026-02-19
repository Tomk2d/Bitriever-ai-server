import requests
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime


class UpbitClientError(Exception):
    """Upbit Client 관련 에러"""
    pass


class UpbitClient:
    """업비트 공개 API 클라이언트 (인증 불필요)"""
    
    def __init__(self, base_url: str = "https://api.upbit.com"):
        self.base_url = base_url
        self.session = requests.Session()
        self.logger = logging.getLogger(__name__)

    def fetch_daily_candles(
        self,
        market: str,
        to: Optional[str] = None,
        count: int = 200,
    ) -> Optional[List[Dict[str, Any]]]:
        """
        일봉 캔들 조회
        
        Args:
            market: 거래쌍 코드 (예: "KRW-BTC")
            to: 조회 종료 시각 (ISO 8601 형식, None이면 현재 시각)
            count: 조회할 캔들 개수 (최대 200, 기본값 200)
            
        Returns:
            캔들 데이터 리스트 또는 None (에러 시)
        """
        try:
            endpoint = "/v1/candles/days"
            url = f"{self.base_url}{endpoint}"
            
            params = {
                "market": market,
                "count": min(count, 200),  # 최대 200개로 제한
            }
            
            if to:
                params["to"] = to
            
            response = self.session.get(url, params=params)
            response.raise_for_status()
            
            data = response.json()
            
            if not isinstance(data, list):
                self.logger.warning(f"Unexpected response format for market {market}")
                return None
                
            return data
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"UpbitClient GET request failed for market {market}: {e}")
            raise UpbitClientError(f"Failed to fetch daily candles for {market}: {e}")
        except Exception as e:
            self.logger.error(f"UpbitClient unexpected error for market {market}: {e}")
            raise UpbitClientError(f"Unexpected error fetching daily candles for {market}: {e}")

