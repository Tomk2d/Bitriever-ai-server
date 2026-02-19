import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP
from model.TradingHistories import TradingHistories


class TradingProfitCalculator:
    """거래 내역을 기반으로 수익률과 평균 구매 단가를 계산하는 클래스"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def calculate_profit_loss(
        self, trading_histories: List[TradingHistories]
    ) -> List[TradingHistories]:
        """
        거래 내역을 순회하며 수익률과 평균 구매 단가를 계산합니다.

        Args:
            trading_histories: trade_time 순으로 정렬된 거래 내역 리스트 (과거부터 현재 순)

        Returns:
            profit_loss_rate와 avg_buy_price가 계산된 거래 내역 리스트
        """
        try:
            # trade_time 순으로 정렬 (과거부터 현재 순)
            sorted_histories = sorted(
                trading_histories, key=lambda x: x.trade_time
            )

            # 보유량 추적 딕셔너리: {coin_id: [avg_buy_price, quantity]}
            holdings: Dict[int, List[Decimal]] = {}

            for history in sorted_histories:
                coin_id = history.coin_id
                trade_type = history.trade_type
                price = Decimal(str(history.price))
                quantity = Decimal(str(history.quantity))

                if trade_type == 0:  # 매수
                    self._process_buy(holdings, coin_id, price, quantity, history)
                elif trade_type == 1:  # 매도
                    self._process_sell(holdings, coin_id, price, quantity, history)

            self.logger.info(
                f"수익률 계산 완료: 총 {len(sorted_histories)}개 거래 내역 처리"
            )
            return sorted_histories

        except Exception as e:
            self.logger.error(f"수익률 계산 중 에러 발생: {e}")
            raise e

    def _process_buy(
        self,
        holdings: Dict[int, List[Decimal]],
        coin_id: int,
        buy_price: Decimal,
        buy_quantity: Decimal,
        history: TradingHistories,
    ):
        """매수 처리: 평균 단가 계산 및 보유량 증가"""
        if coin_id not in holdings:
            # 첫 매수
            holdings[coin_id] = [buy_price, buy_quantity]
        else:
            # 기존 보유량이 있는 경우: 가중 평균 계산
            old_avg_price, old_quantity = holdings[coin_id]

            # 새로운 평균 단가 = (기존 총액 + 신규 총액) / (기존 수량 + 신규 수량)
            old_total = old_avg_price * old_quantity
            new_total = buy_price * buy_quantity
            total_quantity = old_quantity + buy_quantity

            if total_quantity > 0:
                new_avg_price = (old_total + new_total) / total_quantity
                holdings[coin_id] = [new_avg_price, total_quantity]
            else:
                holdings[coin_id] = [buy_price, buy_quantity]

        # 매수 시에는 profit_loss_rate와 avg_buy_price를 NULL로 설정
        history.profit_loss_rate = None
        history.avg_buy_price = None

    def _process_sell(
        self,
        holdings: Dict[int, List[Decimal]],
        coin_id: int,
        sell_price: Decimal,
        sell_quantity: Decimal,
        history: TradingHistories,
    ):
        """매도 처리: 수익률 계산 및 보유량 감소"""
        if coin_id not in holdings or holdings[coin_id][1] <= 0:
            # 보유량이 없거나 매수한 적이 없는 경우
            history.profit_loss_rate = None
            history.avg_buy_price = None
            return

        avg_buy_price, remaining_quantity = holdings[coin_id]

        if remaining_quantity < sell_quantity:
            # 보유량이 매도 수량보다 적은 경우
            history.profit_loss_rate = None
            history.avg_buy_price = None
            return

        # 수익률 계산: ((매도가 - 평균 구매가) / 평균 구매가) * 100
        # 소수점 2째자리까지 반올림
        if avg_buy_price > 0:
            profit_loss_rate = ((sell_price - avg_buy_price) / avg_buy_price) * 100
            # 소수점 2째자리까지 반올림
            profit_loss_rate = profit_loss_rate.quantize(
                Decimal("0.01"), rounding=ROUND_HALF_UP
            )
        else:
            profit_loss_rate = Decimal("0.00")

        # history에 값 설정
        history.profit_loss_rate = float(profit_loss_rate)
        history.avg_buy_price = float(avg_buy_price)

        # 보유량 감소
        new_quantity = remaining_quantity - sell_quantity
        
        if new_quantity <= 0:
            # 보유량이 0이 되면 딕셔너리에서 제거
            del holdings[coin_id]
        else:
            # 평균 단가는 유지 (FIFO가 아닌 평균 단가 방식)
            holdings[coin_id] = [avg_buy_price, new_quantity]

    def calculate_from_json_data(
        self, json_data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        JSON 데이터를 받아서 계산하고 결과를 반환합니다.
        테스트용 메서드입니다.

        Args:
            json_data: response_for_test.json 형식의 데이터

        Returns:
            계산된 거래 내역 리스트
        """
        try:
            if not json_data.get("success") or "data" not in json_data:
                raise ValueError("유효하지 않은 JSON 데이터 형식입니다")

            trading_data = json_data["data"]

            # trade_time 순으로 정렬 (과거부터 현재 순)
            sorted_data = sorted(
                trading_data,
                key=lambda x: datetime.fromisoformat(x["tradeTime"].replace("Z", "+00:00")),
            )

            # 보유량 추적 딕셔너리: {coin_id: [avg_buy_price, quantity]}
            holdings: Dict[int, List[Decimal]] = {}

            for item in sorted_data:
                coin_id = item["coinId"]
                trade_type = item["tradeType"]
                price = Decimal(str(item["price"]))
                quantity = Decimal(str(item["quantity"]))

                if trade_type == 0:  # 매수
                    self._process_buy_json(holdings, coin_id, price, quantity, item)
                elif trade_type == 1:  # 매도
                    self._process_sell_json(holdings, coin_id, price, quantity, item)

            self.logger.info(
                f"JSON 데이터 수익률 계산 완료: 총 {len(sorted_data)}개 거래 내역 처리"
            )
            return sorted_data

        except Exception as e:
            self.logger.error(f"JSON 데이터 수익률 계산 중 에러 발생: {e}")
            raise e

    def _process_buy_json(
        self,
        holdings: Dict[int, List[Decimal]],
        coin_id: int,
        buy_price: Decimal,
        buy_quantity: Decimal,
        item: Dict[str, Any],
    ):
        """매수 처리 (JSON 데이터용)"""
        if coin_id not in holdings:
            holdings[coin_id] = [buy_price, buy_quantity]
        else:
            old_avg_price, old_quantity = holdings[coin_id]
            old_total = old_avg_price * old_quantity
            new_total = buy_price * buy_quantity
            total_quantity = old_quantity + buy_quantity

            if total_quantity > 0:
                new_avg_price = (old_total + new_total) / total_quantity
                holdings[coin_id] = [new_avg_price, total_quantity]
            else:
                holdings[coin_id] = [buy_price, buy_quantity]

        # 매수 시에는 NULL
        item["profitLossRate"] = None
        item["avgBuyPrice"] = None

    def _process_sell_json(
        self,
        holdings: Dict[int, List[Decimal]],
        coin_id: int,
        sell_price: Decimal,
        sell_quantity: Decimal,
        item: Dict[str, Any],
    ):
        """매도 처리 (JSON 데이터용)"""
        if coin_id not in holdings or holdings[coin_id][1] <= 0:
            item["profitLossRate"] = None
            item["avgBuyPrice"] = None
            return

        avg_buy_price, remaining_quantity = holdings[coin_id]

        if remaining_quantity < sell_quantity:
            item["profitLossRate"] = None
            item["avgBuyPrice"] = None
            return

        # 수익률 계산
        if avg_buy_price > 0:
            profit_loss_rate = ((sell_price - avg_buy_price) / avg_buy_price) * 100
            profit_loss_rate = profit_loss_rate.quantize(
                Decimal("0.01"), rounding=ROUND_HALF_UP
            )
        else:
            profit_loss_rate = Decimal("0.00")

        # 결과 저장
        item["profitLossRate"] = float(profit_loss_rate)
        item["avgBuyPrice"] = float(avg_buy_price)

        # 보유량 감소
        new_quantity = remaining_quantity - sell_quantity
        
        if new_quantity <= 0:
            del holdings[coin_id]
        else:
            holdings[coin_id] = [avg_buy_price, new_quantity]

