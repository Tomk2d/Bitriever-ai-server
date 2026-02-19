"""
테스트 데이터를 사용하여 수익률 계산 로직을 테스트하는 스크립트
"""
import json
import sys
import logging
from pathlib import Path

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "src" / "app-server"))

from service.trading_profit_calculator import TradingProfitCalculator


def main():
    # 테스트 데이터 로드
    test_data_path = project_root / "testData" / "response_for_test.json"
    
    with open(test_data_path, "r", encoding="utf-8") as f:
        json_data = json.load(f)

    # 계산기 인스턴스 생성
    calculator = TradingProfitCalculator()

    # 계산 실행
    print("=" * 80)
    print("수익률 계산 시작")
    print("=" * 80)
    
    result = calculator.calculate_from_json_data(json_data)

    # 결과 출력 (매도 거래만 필터링하여 확인)
    print("\n매도 거래 내역 (수익률 계산 결과):")
    print("-" * 80)
    
    sell_trades = [item for item in result if item["tradeType"] == 1]
    
    for item in sell_trades[:20]:  # 처음 20개만 출력
        coin_symbol = item["coin"]["symbol"]
        trade_time = item["tradeTime"]
        sell_price = item["price"]
        quantity = item["quantity"]
        profit_loss_rate = item.get("profitLossRate")
        avg_buy_price = item.get("avgBuyPrice")
        
        if profit_loss_rate is not None:
            status = "✅ 계산 완료"
            print(
                f"{status} | {coin_symbol:6s} | "
                f"매도가: {sell_price:>12,.0f} | "
                f"수량: {quantity:>10.4f} | "
                f"평단: {avg_buy_price:>12,.0f} | "
                f"수익률: {profit_loss_rate:>7.2f}% | "
                f"{trade_time}"
            )
        else:
            status = "❌ 계산 불가"
            print(
                f"{status} | {coin_symbol:6s} | "
                f"매도가: {sell_price:>12,.0f} | "
                f"수량: {quantity:>10.4f} | "
                f"보유량 부족 또는 매수 이력 없음 | "
                f"{trade_time}"
            )

    # 통계 출력
    print("\n" + "=" * 80)
    print("통계:")
    print("-" * 80)
    
    total_trades = len(result)
    buy_trades = len([item for item in result if item["tradeType"] == 0])
    sell_trades = len([item for item in result if item["tradeType"] == 1])
    calculated_sells = len([item for item in result if item.get("profitLossRate") is not None])
    
    print(f"총 거래 내역: {total_trades}개")
    print(f"  - 매수: {buy_trades}개")
    print(f"  - 매도: {sell_trades}개")
    print(f"  - 수익률 계산 완료: {calculated_sells}개")
    print(f"  - 수익률 계산 실패: {sell_trades - calculated_sells}개")
    
    # 수익률이 계산된 매도 거래의 평균 수익률
    profit_rates = [
        item["profitLossRate"]
        for item in result
        if item.get("profitLossRate") is not None
    ]
    
    if profit_rates:
        avg_profit = sum(profit_rates) / len(profit_rates)
        print(f"\n평균 수익률: {avg_profit:.2f}%")
        print(f"최고 수익률: {max(profit_rates):.2f}%")
        print(f"최저 수익률: {min(profit_rates):.2f}%")
    
    # 특정 코인 예시 출력 (SOL)
    print("\n" + "=" * 80)
    print("SOL 코인 거래 내역 예시 (최근 10개):")
    print("-" * 80)
    
    sol_trades = [
        item for item in result
        if item["coin"]["symbol"] == "SOL"
    ][-10:]  # 최근 10개
    
    for item in sol_trades:
        trade_type = "매수" if item["tradeType"] == 0 else "매도"
        price = item["price"]
        quantity = item["quantity"]
        profit_loss_rate = item.get("profitLossRate")
        avg_buy_price = item.get("avgBuyPrice")
        
        if trade_type == "매도" and profit_loss_rate is not None:
            print(
                f"{trade_type:4s} | 가격: {price:>12,.0f} | "
                f"수량: {quantity:>10.4f} | "
                f"평단: {avg_buy_price:>12,.0f} | "
                f"수익률: {profit_loss_rate:>7.2f}% | "
                f"{item['tradeTime']}"
            )
        else:
            print(
                f"{trade_type:4s} | 가격: {price:>12,.0f} | "
                f"수량: {quantity:>10.4f} | "
                f"{item['tradeTime']}"
            )

    print("\n" + "=" * 80)
    print("계산 완료!")
    print("=" * 80)


if __name__ == "__main__":
    main()

