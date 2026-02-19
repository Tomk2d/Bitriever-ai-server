import logging
import uuid
from typing import List, Dict, Any, Optional
from decimal import Decimal
from model.TradingHistories import TradingHistories
from model.CoinHoldingsPast import CoinHoldingsPast
from service.trading_profit_calculator import TradingProfitCalculator
from repository.trading_histories_repository import TradingHistoriesRepository
from repository.coin_holdings_past_repository import CoinHoldingsPastRepository
from repository.coin_repository import CoinRepository
from dto.exchange_credentials_dto import ExchangeProvider


class TradingProfitService:
    """거래 내역 수익률 계산 및 보유 종목 평단 관리 서비스"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self._trading_profit_calculator = None
        self._trading_histories_repository = None
        self._coin_holdings_past_repository = None
        self._coin_repository = None

    @property
    def trading_profit_calculator(self):
        if self._trading_profit_calculator is None:
            self._trading_profit_calculator = TradingProfitCalculator()
        return self._trading_profit_calculator

    @property
    def trading_histories_repository(self):
        if self._trading_histories_repository is None:
            self._trading_histories_repository = TradingHistoriesRepository()
        return self._trading_histories_repository

    @property
    def coin_holdings_past_repository(self):
        if self._coin_holdings_past_repository is None:
            self._coin_holdings_past_repository = CoinHoldingsPastRepository()
        return self._coin_holdings_past_repository

    @property
    def coin_repository(self):
        if self._coin_repository is None:
            self._coin_repository = CoinRepository()
        return self._coin_repository

    def calculate_and_update_profit_loss(
        self, user_id: str, exchange_code: int, is_initial: bool = False
    ) -> Dict[str, Any]:
        """
        거래 내역 수익률 계산 및 업데이트, 보유 종목 평단 저장
        
        Args:
            user_id: 사용자 UUID
            exchange_code: 거래소 코드
            is_initial: 최초 fetch 여부 (True: 최초, False: 이후 업데이트)
        
        Returns:
            {
                "updated_count": int,
                "holdings_count": int,
                "deleted_holdings_count": int
            }
        """
        try:
            # 1. 사용자의 거래 내역 조회 (trade_time 순으로 정렬)
            trading_histories = (
                self.trading_histories_repository.find_by_user_and_exchange(
                    user_id, exchange_code
                )
            )

            if not trading_histories:
                self.logger.warning(
                    f"거래 내역이 없습니다: user_id={user_id}, exchange_code={exchange_code}"
                )
                return {
                    "updated_count": 0,
                    "holdings_count": 0,
                    "deleted_holdings_count": 0,
                }

            # 2. 기존 보유 종목 평단 조회
            holdings_dict = self.coin_holdings_past_repository.get_holdings_dict(
                user_id, exchange_code
            )

            # 3. is_initial 재확인: coin_holdings_past에 데이터가 없으면 최초로 판단
            # coin_holdings_past 테이블에 실제 데이터가 있는지 확인하는 것이 더 정확함
            if not holdings_dict:
                is_initial = True
                self.logger.info(
                    f"coin_holdings_past에 데이터가 없어 최초 계산으로 판단: user_id={user_id}, exchange_code={exchange_code}"
                )
            else:
                is_initial = False
                self.logger.info(
                    f"coin_holdings_past에 데이터가 있어 이후 업데이트로 판단: user_id={user_id}, exchange_code={exchange_code}, holdings_count={len(holdings_dict)}"
                )

            # 4. 수익률 계산
            # 최초가 아닌 경우, 기존 보유 종목 평단을 사용하여 계산
            if not is_initial and holdings_dict:
                updated_histories = self._calculate_with_existing_holdings(
                    trading_histories, holdings_dict
                )
            else:
                # 최초인 경우, 전체 거래 내역을 순회하며 계산
                updated_histories = (
                    self.trading_profit_calculator.calculate_profit_loss(
                        trading_histories
                    )
                )

            # 5. 거래 내역 업데이트
            updated_count = len(updated_histories)
            self.trading_histories_repository.update_profit_loss(updated_histories)

            # 6. 보유 종목 평단 계산 및 저장
            final_holdings = self._calculate_final_holdings(updated_histories)
            holdings_count = len(final_holdings)

            # 7. 보유 종목 평단 저장/업데이트
            self.coin_holdings_past_repository.save_or_update_holdings(
                user_id, exchange_code, final_holdings
            )

            # 8. 보유 수량이 0인 종목 삭제
            coin_ids_with_holdings = {
                coin_id
                for coin_id, data in final_holdings.items()
                if data["remaining_quantity"] > 0
            }
            deleted_count = (
                self.coin_holdings_past_repository.delete_holdings_not_in_list(
                    user_id, exchange_code, coin_ids_with_holdings
                )
            )

            self.logger.info(
                f"수익률 계산 및 업데이트 완료: user_id={user_id}, exchange_code={exchange_code}, "
                f"updated={updated_count}, holdings={holdings_count}, deleted={deleted_count}"
            )

            return {
                "updated_count": updated_count,
                "holdings_count": holdings_count,
                "deleted_holdings_count": deleted_count,
            }

        except Exception as e:
            self.logger.error(f"수익률 계산 및 업데이트 중 에러 발생: {e}")
            raise e

    def _calculate_with_existing_holdings(
        self,
        trading_histories: List[TradingHistories],
        existing_holdings: Dict[int, Dict],
    ) -> List[TradingHistories]:
        """
        기존 보유 종목 평단을 사용하여 수익률 계산 (이후 업데이트인 경우)
        
        Args:
            trading_histories: 거래 내역 목록
            existing_holdings: 기존 보유 종목 평단 딕셔너리
        
        Returns:
            수익률이 계산된 거래 내역 목록
        """
        try:
            # trade_time 순으로 정렬 (과거부터 현재 순)
            sorted_histories = sorted(
                trading_histories, key=lambda x: x.trade_time
            )

            # 기존 보유 종목 평단을 holdings 딕셔너리로 변환
            holdings: Dict[int, List[Decimal]] = {}
            for coin_id, data in existing_holdings.items():
                holdings[coin_id] = [
                    Decimal(str(data["avg_buy_price"])),
                    Decimal(str(data["remaining_quantity"])),
                ]

            # 새로운 거래 내역만 순회하며 계산
            for history in sorted_histories:
                coin_id = history.coin_id
                trade_type = history.trade_type
                price = Decimal(str(history.price))
                quantity = Decimal(str(history.quantity))

                if trade_type == 0:  # 매수
                    self.trading_profit_calculator._process_buy(
                        holdings, coin_id, price, quantity, history
                    )
                elif trade_type == 1:  # 매도
                    self.trading_profit_calculator._process_sell(
                        holdings, coin_id, price, quantity, history
                    )

            return sorted_histories

        except Exception as e:
            self.logger.error(f"기존 보유 종목 평단을 사용한 수익률 계산 중 에러 발생: {e}")
            raise e

    def _calculate_final_holdings(
        self, trading_histories: List[TradingHistories]
    ) -> Dict[int, Dict]:
        """
        최종 보유 종목 평단 계산
        
        Args:
            trading_histories: 거래 내역 목록
        
        Returns:
            {coin_id: {"symbol": str, "avg_buy_price": Decimal, "remaining_quantity": Decimal}}
        """
        try:
            # trade_time 순으로 정렬 (과거부터 현재 순)
            sorted_histories = sorted(
                trading_histories, key=lambda x: x.trade_time
            )

            # 보유량 추적 딕셔너리: {coin_id: [avg_buy_price, quantity]}
            holdings: Dict[int, List[Decimal]] = {}
            # 코인 심볼 추적: {coin_id: symbol}
            coin_symbols: Dict[int, str] = {}
            
            # 모든 코인 정보 조회
            coins = self.coin_repository.get_all_coins()
            coin_map = {coin.id: coin.symbol for coin in coins}

            for history in sorted_histories:
                coin_id = history.coin_id
                trade_type = history.trade_type
                price = Decimal(str(history.price))
                quantity = Decimal(str(history.quantity))

                # 코인 심볼 저장 (첫 거래에서)
                if coin_id not in coin_symbols:
                    coin_symbols[coin_id] = coin_map.get(coin_id, "UNKNOWN")

                if trade_type == 0:  # 매수
                    self.trading_profit_calculator._process_buy(
                        holdings, coin_id, price, quantity, history
                    )
                elif trade_type == 1:  # 매도
                    self.trading_profit_calculator._process_sell(
                        holdings, coin_id, price, quantity, history
                    )

            # 최종 보유 종목 딕셔너리 생성
            final_holdings = {}
            for coin_id, (avg_buy_price, remaining_quantity) in holdings.items():
                if remaining_quantity > 0:  # 보유 수량이 0보다 큰 경우만 저장
                    final_holdings[coin_id] = {
                        "symbol": coin_symbols.get(coin_id, "UNKNOWN"),
                        "avg_buy_price": avg_buy_price,
                        "remaining_quantity": remaining_quantity,
                    }

            return final_holdings

        except Exception as e:
            self.logger.error(f"최종 보유 종목 평단 계산 중 에러 발생: {e}")
            raise e

