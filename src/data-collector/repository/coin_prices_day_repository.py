import logging
from typing import List, Optional
from datetime import datetime
from sqlalchemy import and_
import sys
from pathlib import Path

# app-server 모듈 경로 추가
app_server_path = Path(__file__).parent.parent.parent / "app-server"
sys.path.insert(0, str(app_server_path))

from database.database_connection import db
from model.CoinPricesDay import CoinPricesDay


class CoinPricesDayRepository:
    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def save_candle_list(self, candle_list: List[CoinPricesDay]) -> int:
        """
        캔들 데이터 리스트를 배치로 저장
        
        Args:
            candle_list: 저장할 캔들 데이터 리스트
            
        Returns:
            저장된 행 수
        """
        session = None
        try:
            session = db.get_session()
            
            saved_count = 0
            for candle in candle_list:
                # 중복 체크 (market_code + candle_date_time_utc)
                existing = session.query(CoinPricesDay).filter(
                    and_(
                        CoinPricesDay.market_code == candle.market_code,
                        CoinPricesDay.candle_date_time_utc == candle.candle_date_time_utc
                    )
                ).first()
                
                if not existing:
                    session.add(candle)
                    saved_count += 1
            
            session.commit()
            self.logger.info(f"Saved {saved_count} candles out of {len(candle_list)}")
            return saved_count
            
        except Exception as e:
            self.logger.error(f"캔들 데이터 저장 중 에러 발생: {e}")
            if session:
                session.rollback()
            raise e
        finally:
            if session:
                session.close()

    def get_latest_candle_date(self, coin_id: int) -> Optional[datetime]:
        """
        특정 코인의 최신 캔들 날짜 조회 (증분 수집용)
        
        Args:
            coin_id: 코인 ID
            
        Returns:
            최신 캔들의 candle_date_time_utc 또는 None
        """
        session = None
        try:
            session = db.get_session()
            latest = session.query(CoinPricesDay).filter(
                CoinPricesDay.coin_id == coin_id
            ).order_by(CoinPricesDay.candle_date_time_utc.desc()).first()
            
            if latest:
                return latest.candle_date_time_utc
            return None
            
        except Exception as e:
            self.logger.error(f"최신 캔들 날짜 조회 중 에러 발생: {e}")
            raise e
        finally:
            if session:
                session.close()

    def check_candle_exists(
        self, market_code: str, candle_date_time_utc: datetime
    ) -> bool:
        """
        특정 캔들이 이미 존재하는지 확인
        
        Args:
            market_code: 거래쌍 코드
            candle_date_time_utc: 캔들 날짜 (UTC)
            
        Returns:
            존재 여부
        """
        session = None
        try:
            session = db.get_session()
            existing = session.query(CoinPricesDay).filter(
                and_(
                    CoinPricesDay.market_code == market_code,
                    CoinPricesDay.candle_date_time_utc == candle_date_time_utc
                )
            ).first()
            
            return existing is not None
            
        except Exception as e:
            self.logger.error(f"캔들 존재 확인 중 에러 발생: {e}")
            raise e
        finally:
            if session:
                session.close()

