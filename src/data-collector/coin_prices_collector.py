import logging
import time
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Semaphore
import sys
from pathlib import Path
import pytz

# app-server 모듈 경로 추가
app_server_path = Path(__file__).parent.parent / "app-server"
sys.path.insert(0, str(app_server_path))

# 프로젝트 루트 경로 추가 (data-collector 모듈 import용)
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# data-collector 디렉토리 경로 추가 (repository import용)
data_collector_path = Path(__file__).parent
sys.path.insert(0, str(data_collector_path))

from database.database_connection import db
from model.Coins import Coins
from model.CoinPricesDay import CoinPricesDay
from upbit_client import UpbitClient, UpbitClientError
from repository.coin_prices_day_repository import CoinPricesDayRepository


class CoinPricesCollector:
    """일봉 캔들 데이터 수집기"""
    
    def __init__(self, max_workers: int = 2):
        """
        Args:
            max_workers: 병렬 처리 최대 워커 수 (Rate limit 고려: 초당 2회, 워커당 0.5초 간격)
        """
        self.logger = logging.getLogger(__name__)
        self.upbit_client = UpbitClient()
        self.repository = CoinPricesDayRepository()
        self.max_workers = max_workers
        # Rate limit: 초당 2회 제한을 위한 세마포어
        self.rate_limiter = Semaphore(2)
        self.request_lock = Semaphore(1)  # 요청 간격 제어용
        self.last_request_time = 0.0

    def _wait_for_rate_limit(self):
        """Rate limit 준수 (초당 2회, 0.5초 간격)"""
        current_time = time.time()
        time_since_last_request = current_time - self.last_request_time
        
        if time_since_last_request < 0.5:  # 최소 0.5초 간격 (초당 2회)
            sleep_time = 0.5 - time_since_last_request
            time.sleep(sleep_time)
        
        self.last_request_time = time.time()

    def _fetch_and_save_candles(
        self,
        coin: Coins,
        start_date: datetime,
        end_date: datetime,
    ) -> Dict[str, Any]:
        """
        단일 코인의 캔들 데이터를 수집하고 저장
        
        Args:
            coin: 코인 정보
            start_date: 수집 시작 날짜
            end_date: 수집 종료 날짜
            
        Returns:
            수집 결과 딕셔너리
        """
        result = {
            "coin_id": coin.id,
            "market_code": coin.market_code,
            "total_fetched": 0,
            "total_saved": 0,
            "error": None,
        }
        
        try:
            # 타임존 정보 확인 및 변환 (모든 날짜를 UTC로 통일)
            if start_date.tzinfo is None:
                start_date = pytz.UTC.localize(start_date)
            else:
                start_date = start_date.astimezone(pytz.UTC)
            
            if end_date.tzinfo is None:
                end_date = pytz.UTC.localize(end_date)
            else:
                end_date = end_date.astimezone(pytz.UTC)
            
            # Rate limit 준수
            with self.rate_limiter:
                self._wait_for_rate_limit()
                
                # end_date부터 start_date까지 역순으로 수집
                current_to = end_date
                all_candles = []
                
                while current_to > start_date:
                    try:
                        # ISO 8601 형식으로 변환 (UTC 기준, 타임존 정보 포함)
                        if current_to.tzinfo:
                            to_str = current_to.strftime("%Y-%m-%dT%H:%M:%S%z")
                            # +0000 형식을 +00:00 형식으로 변환
                            if to_str.endswith("+0000"):
                                to_str = to_str.replace("+0000", "+00:00")
                            elif to_str.endswith("-0000"):
                                to_str = to_str.replace("-0000", "+00:00")
                        else:
                            to_str = current_to.strftime("%Y-%m-%dT%H:%M:%S")
                        
                        candles = self.upbit_client.fetch_daily_candles(
                            market=coin.market_code,
                            to=to_str,
                            count=200,
                        )
                        
                        if not candles or len(candles) == 0:
                            break
                        
                        # 캔들 데이터를 모델로 변환
                        coin_candles = self._convert_to_models(coin, candles)
                        all_candles.extend(coin_candles)
                        result["total_fetched"] += len(candles)
                        
                        # 다음 배치를 위한 to 파라미터 업데이트
                        # 가장 오래된 캔들의 날짜를 사용
                        oldest_candle = min(candles, key=lambda x: x.get("candle_date_time_utc", ""))
                        oldest_date_str = oldest_candle.get("candle_date_time_utc")
                        
                        if oldest_date_str:
                            # 문자열을 datetime으로 변환 (UTC)
                            oldest_date = datetime.fromisoformat(
                                oldest_date_str.replace("Z", "+00:00")
                            )
                            # 타임존 정보가 없으면 UTC로 설정
                            if oldest_date.tzinfo is None:
                                oldest_date = pytz.UTC.localize(oldest_date)
                            else:
                                oldest_date = oldest_date.astimezone(pytz.UTC)
                            
                            # start_date와 비교 (둘 다 UTC)
                            if oldest_date <= start_date:
                                break
                            current_to = oldest_date - timedelta(days=1)
                        else:
                            break
                        
                        # 200개 미만이면 더 이상 데이터가 없음
                        if len(candles) < 200:
                            break
                        
                        # 한 배치(200개) 요청 후 1초 대기 (Rate limit 방지)
                        time.sleep(1)
                            
                    except UpbitClientError as e:
                        error_msg = str(e)
                        # Rate limit 에러(429)인 경우 재시도
                        if "429" in error_msg or "Too Many Requests" in error_msg:
                            self.logger.warning(f"Rate limit 에러 발생 {coin.market_code}, 2초 대기 후 재시도...")
                            time.sleep(2)
                            continue  # 재시도
                        else:
                            self.logger.error(f"API 호출 실패 {coin.market_code}: {e}")
                            result["error"] = error_msg
                            break
                    except Exception as e:
                        self.logger.error(f"캔들 수집 중 에러 {coin.market_code}: {e}")
                        result["error"] = str(e)
                        break
                
                # 수집한 데이터 저장
                if all_candles:
                    saved_count = self.repository.save_candle_list(all_candles)
                    result["total_saved"] = saved_count
                    self.logger.info(
                        f"{coin.market_code}: 수집 {result['total_fetched']}개, 저장 {saved_count}개"
                    )
                else:
                    self.logger.warning(f"{coin.market_code}: 수집된 데이터가 없습니다")
                    
        except Exception as e:
            self.logger.error(f"{coin.market_code} 수집 중 예상치 못한 에러: {e}")
            result["error"] = str(e)
        
        return result

    def _convert_to_models(
        self, coin: Coins, candles: List[Dict[str, Any]]
    ) -> List[CoinPricesDay]:
        """
        API 응답을 CoinPricesDay 모델로 변환
        
        Args:
            coin: 코인 정보
            candles: API 응답 캔들 리스트
            
        Returns:
            CoinPricesDay 모델 리스트
        """
        models = []
        
        for candle_data in candles:
            try:
                # 날짜 문자열을 datetime으로 변환
                date_utc_str = candle_data.get("candle_date_time_utc", "")
                date_kst_str = candle_data.get("candle_date_time_kst", "")
                
                # ISO 8601 형식 파싱
                date_utc = datetime.fromisoformat(date_utc_str.replace("Z", "+00:00"))
                date_kst = datetime.fromisoformat(date_kst_str.replace("Z", "+00:00"))
                
                # None 값을 0으로 처리
                prev_closing_price = candle_data.get("prev_closing_price")
                change_price = candle_data.get("change_price")
                change_rate = candle_data.get("change_rate")
                timestamp = candle_data.get("timestamp")
                
                model = CoinPricesDay(
                    coin_id=coin.id,
                    market_code=candle_data.get("market", ""),
                    candle_date_time_utc=date_utc,
                    candle_date_time_kst=date_kst,
                    opening_price=candle_data.get("opening_price", 0),
                    high_price=candle_data.get("high_price", 0),
                    low_price=candle_data.get("low_price", 0),
                    trade_price=candle_data.get("trade_price", 0),
                    timestamp=timestamp if timestamp is not None else 0,
                    candle_acc_trade_price=candle_data.get("candle_acc_trade_price", 0),
                    candle_acc_trade_volume=candle_data.get("candle_acc_trade_volume", 0),
                    prev_closing_price=prev_closing_price if prev_closing_price is not None else 0,
                    change_price=change_price if change_price is not None else 0,
                    change_rate=change_rate if change_rate is not None else 0,
                    converted_trade_price=candle_data.get("converted_trade_price"),
                )
                models.append(model)
                
            except Exception as e:
                self.logger.warning(f"캔들 데이터 변환 실패: {candle_data}, 에러: {e}")
                continue
        
        return models

    def sync_all_coins_daily_candles(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """
        모든 코인의 일봉 데이터를 수집
        
        Args:
            start_date: 수집 시작 날짜 (기본값: 2017-01-01)
            end_date: 수집 종료 날짜 (기본값: 현재 날짜)
            
        Returns:
            수집 결과 요약
        """
        # 기본값 설정
        if start_date is None:
            start_date = datetime(2017, 1, 1, tzinfo=pytz.UTC)
        if end_date is None:
            end_date = datetime.now(pytz.UTC)
        
        # 타임존이 없으면 UTC로 설정
        if start_date.tzinfo is None:
            start_date = pytz.UTC.localize(start_date)
        if end_date.tzinfo is None:
            end_date = pytz.UTC.localize(end_date)
        
        self.logger.info(
            f"전체 코인 일봉 데이터 수집 시작: {start_date} ~ {end_date}"
        )
        
        # 활성 코인 목록 조회
        session = db.get_session()
        try:
            coins = session.query(Coins).filter(Coins.is_active == True).all()
            self.logger.info(f"수집 대상 코인 수: {len(coins)}")
        except Exception as e:
            self.logger.error(f"코인 목록 조회 실패: {e}")
            raise
        finally:
            session.close()
        
        # 병렬 처리로 수집
        results = []
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {
                executor.submit(
                    self._fetch_and_save_candles, coin, start_date, end_date
                ): coin
                for coin in coins
            }
            
            for future in as_completed(futures):
                coin = futures[future]
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    self.logger.error(f"{coin.market_code} 수집 중 예외: {e}")
                    results.append({
                        "coin_id": coin.id,
                        "market_code": coin.market_code,
                        "total_fetched": 0,
                        "total_saved": 0,
                        "error": str(e),
                    })
        
        # 결과 요약
        summary = {
            "total_coins": len(coins),
            "success_count": sum(1 for r in results if r.get("error") is None),
            "error_count": sum(1 for r in results if r.get("error") is not None),
            "total_fetched": sum(r.get("total_fetched", 0) for r in results),
            "total_saved": sum(r.get("total_saved", 0) for r in results),
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "results": results,
        }
        
        self.logger.info(
            f"수집 완료: 성공 {summary['success_count']}/{summary['total_coins']}, "
            f"수집 {summary['total_fetched']}개, 저장 {summary['total_saved']}개"
        )
        
        return summary

    def sync_single_coin_daily_candles(
        self,
        market_code: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """
        단일 코인의 일봉 데이터를 수집
        
        Args:
            market_code: 거래쌍 코드 (예: "KRW-BTC")
            start_date: 수집 시작 날짜 (기본값: 2017-01-01)
            end_date: 수집 종료 날짜 (기본값: 현재 날짜)
            
        Returns:
            수집 결과
        """
        # 기본값 설정
        if start_date is None:
            start_date = datetime(2017, 1, 1, tzinfo=pytz.UTC)
        if end_date is None:
            end_date = datetime.now(pytz.UTC)
        
        # 타임존이 없으면 UTC로 설정
        if start_date.tzinfo is None:
            start_date = pytz.UTC.localize(start_date)
        if end_date.tzinfo is None:
            end_date = pytz.UTC.localize(end_date)
        
        # 코인 정보 조회
        session = db.get_session()
        try:
            coin = session.query(Coins).filter(
                Coins.market_code == market_code
            ).first()
            
            if not coin:
                raise ValueError(f"코인을 찾을 수 없습니다: {market_code}")
            
            self.logger.info(
                f"{market_code} 일봉 데이터 수집 시작: {start_date} ~ {end_date}"
            )
            
            result = self._fetch_and_save_candles(coin, start_date, end_date)
            
            return {
                "market_code": market_code,
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                **result,
            }
            
        except Exception as e:
            self.logger.error(f"{market_code} 수집 실패: {e}")
            raise
        finally:
            session.close()

