from dotenv import load_dotenv
import logging
from datetime import datetime
import pytz
import time
from typing import List, Dict, Any, Optional
from fastapi import HTTPException
from model.TradingHistories import TradingHistories

load_dotenv()


class TradingHistoriesService:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self._trading_repository = None
        self._coin_repository = None
        self._exchange_credentials_service = None
        self._upbit_service = None

    @property
    def trading_repository(self):
        if self._trading_repository is None:
            from repository.trading_histories_repository import (
                TradingHistoriesRepository,
            )

            self._trading_repository = TradingHistoriesRepository()
        return self._trading_repository

    @property
    def coin_repository(self):
        if self._coin_repository is None:
            from dependencies import get_coin_repository

            self._coin_repository = get_coin_repository()
        return self._coin_repository

    @property
    def exchange_credentials_service(self):
        if self._exchange_credentials_service is None:
            from dependencies import get_exchange_credentials_service

            self._exchange_credentials_service = get_exchange_credentials_service()
        return self._exchange_credentials_service

    @property
    def upbit_service(self):
        if self._upbit_service is None:
            from dependencies import get_upbit_service

            self._upbit_service = get_upbit_service()
        return self._upbit_service

    def get_trading_histories(
        self,
        user_id: str,
        exchange_provider: str,
        start_time: Optional[datetime] = None,
    ):
        try:
            from dto.exchange_credentials_dto import ExchangeProvider

            credentials = self.exchange_credentials_service.get_credentials(
                user_id, ExchangeProvider[exchange_provider]
            )
            if credentials is None:
                raise HTTPException(status_code=404, detail="User not found")

            access_key = credentials.access_key
            secret_key = credentials.secret_key

            uuids = self.upbit_service.fetch_all_trading_uuids(
                access_key, secret_key, start_time
            )

            trading_histies = self.upbit_service.fetch_all_trading_history(
                access_key, secret_key, uuids
            )

            return trading_histies
        except Exception as e:
            raise e

    def process_trading_histories(
        self,
        user_id: str,
        exchange_provider: str,
        trading_histies: List[Dict[str, Any]],
    ):
        try:
            from dependencies import get_coin_repository
            from dto.exchange_credentials_dto import ExchangeProvider

            coin_repository = get_coin_repository()
            coins = coin_repository.get_all_coins()

            coin_map = {str(coin.market_code): coin.id for coin in coins}

            # exchange_provider를 숫자로 변환
            exchange_code = ExchangeProvider[exchange_provider.upper()].value

            trading_history_array = []

            for trading_history in trading_histies:
                if trading_history.get("trades") is None:
                    continue

                total_quantity = 0
                total_price = 0
                for trade in trading_history.get("trades", []):
                    # 문자열을 숫자로 변환
                    volume = float(trade.get("volume", 0))
                    funds = float(trade.get("funds", 0))

                    total_quantity += volume
                    total_price += funds

                avg_price = total_price / total_quantity if total_quantity > 0 else 0

                # trade_type을 숫자로 변환
                trade_type_str = trading_history.get("side", "")
                if trade_type_str == "bid":
                    trade_type = 0  # 매수
                elif trade_type_str == "ask":
                    trade_type = 1  # 매도
                else:
                    trade_type = 0  # 기본값

                trading_histories = TradingHistories(
                    user_id=user_id,
                    coin_id=coin_map[str(trading_history.get("market"))],
                    exchange_code=exchange_code,
                    trade_uuid=trading_history.get("uuid"),
                    trade_type=trade_type,  # 숫자로 변환된 값 사용
                    price=avg_price,
                    quantity=total_quantity,
                    total_price=total_price,
                    fee=float(trading_history.get("paid_fee", 0)),
                    trade_time=trading_history.get("created_at"),
                )
                trading_history_array.append(trading_histories)

            return trading_history_array
        except Exception as e:
            raise e

    def save_trading_histories(
        self, trading_histories: List[TradingHistories]
    ) -> List[TradingHistories]:
        """거래내역 목록 저장"""
        try:
            if not trading_histories:
                return []

            saved_histories = self.trading_repository.save_trading_histories(
                trading_histories
            )

            self.logger.info(f"거래내역 저장 완료: {len(saved_histories)}개")
            return saved_histories

        except Exception as e:
            raise e

    def get_all_trading_histories_by_user(self, user_id: str) -> List[TradingHistories]:
        """사용자의 모든 거래내역 조회"""
        try:
            histories = self.trading_repository.find_by_user_id(user_id)
            self.logger.info(
                f"사용자 {user_id}의 거래내역 조회 완료: {len(histories)}개"
            )
            return histories
        except Exception as e:
            raise e

    def get_all_trading_histories_by_user_formatted(self, user_id: str) -> dict:
        """사용자의 모든 거래내역을 포맷된 형태로 조회"""
        try:
            histories = self.trading_repository.find_by_user_id(user_id)

            formatted_histories = []
            for history in histories:
                try:
                    # Decimal을 안전하게 float로 변환
                    def safe_float(value):
                        if value is None:
                            return 0.0
                        try:
                            return float(str(value))
                        except (ValueError, TypeError):
                            return 0.0

                    formatted_history = {
                        "id": history.id,
                        "coin_id": history.coin_id,
                        "exchange_code": history.exchange_code,
                        "trade_uuid": str(history.trade_uuid),
                        "trade_type": history.trade_type,
                        "price": safe_float(history.price),
                        "quantity": safe_float(history.quantity),
                        "total_price": safe_float(history.total_price),
                        "fee": safe_float(history.fee),
                        "trade_time": (
                            history.trade_time.isoformat()
                            if history.trade_time is not None
                            else None
                        ),
                        "created_at": (
                            history.created_at.isoformat()
                            if history.created_at is not None
                            else None
                        ),
                    }
                    formatted_histories.append(formatted_history)
                except Exception as e:
                    self.logger.warning(
                        f"거래내역 포맷 중 오류 발생 (ID: {history.id}): {e}"
                    )
                    continue

            self.logger.info(
                f"사용자 {user_id}의 거래내역 조회 완료: {len(histories)}개"
            )
            return {
                "total_count": len(histories),
                "trading_histories": formatted_histories,
            }
        except Exception as e:
            raise e
