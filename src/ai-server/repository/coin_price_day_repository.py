import logging
from datetime import datetime
from typing import List

from database.database_connection import db
from model.CoinPricesDay import CoinPricesDay


class CoinPriceDayRepository:
    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def find_by_market_code_and_date_range(
        self,
        session,
        market_code: str,
        start_dt: datetime,
        end_dt: datetime,
    ) -> List[CoinPricesDay]:
        """market_code와 candle_date_time_utc 구간으로 조회, 날짜 오름차순."""
        return (
            session.query(CoinPricesDay)
            .filter(
                CoinPricesDay.market_code == market_code,
                CoinPricesDay.candle_date_time_utc >= start_dt,
                CoinPricesDay.candle_date_time_utc < end_dt,
            )
            .order_by(CoinPricesDay.candle_date_time_utc.asc())
            .all()
        )

    def find_by_coin_id_and_date_range(
        self,
        session,
        coin_id: int,
        start_dt: datetime,
        end_dt: datetime,
    ) -> List[CoinPricesDay]:
        """coin_id와 candle_date_time_utc 구간으로 조회, 날짜 오름차순."""
        return (
            session.query(CoinPricesDay)
            .filter(
                CoinPricesDay.coin_id == coin_id,
                CoinPricesDay.candle_date_time_utc >= start_dt,
                CoinPricesDay.candle_date_time_utc < end_dt,
            )
            .order_by(CoinPricesDay.candle_date_time_utc.asc())
            .all()
        )
