#!/usr/bin/env python3
"""
업비트 일봉 캔들 데이터 수집 스크립트

사용법:
    # 전체 코인 수집 (2017-01-01 ~ 현재)
    python collect_coin_prices.py

    # 전체 코인 수집 (특정 기간)
    python collect_coin_prices.py --start-date 2020-01-01 --end-date 2023-12-31

    # 특정 코인 수집
    python collect_coin_prices.py --market-code KRW-BTC

    # 특정 코인 수집 (특정 기간)
    python collect_coin_prices.py --market-code KRW-BTC --start-date 2020-01-01 --end-date 2023-12-31
"""
import argparse
import logging
import sys
from datetime import datetime
from pathlib import Path
import pytz

# 프로젝트 루트 경로 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# app-server 모듈 경로 추가
app_server_path = project_root / "app-server"
sys.path.insert(0, str(app_server_path))

# data-collector 디렉토리 경로 추가
data_collector_path = Path(__file__).parent
sys.path.insert(0, str(data_collector_path))

# SQLAlchemy 관계를 위해 모든 모델을 명시적으로 import
import model.Users
import model.ExchangeCredentials
import model.Coins
import model.TradingHistories
import model.Assets
import model.CoinHoldingsPast
import model.CoinPricesDay

from coin_prices_collector import CoinPricesCollector


def setup_logging():
    """로깅 설정"""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def parse_date(date_str: str) -> datetime:
    """날짜 문자열을 datetime으로 변환"""
    try:
        # YYYY-MM-DD 형식
        dt = datetime.strptime(date_str, "%Y-%m-%d")
        # UTC로 변환
        return pytz.UTC.localize(dt)
    except ValueError:
        raise argparse.ArgumentTypeError(
            f"날짜 형식이 올바르지 않습니다: {date_str} (예: 2020-01-01)"
        )


def main():
    parser = argparse.ArgumentParser(
        description="업비트 일봉 캔들 데이터 수집",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    
    parser.add_argument(
        "--market-code",
        type=str,
        help="거래쌍 코드 (예: KRW-BTC). 지정하지 않으면 전체 코인 수집",
    )
    
    parser.add_argument(
        "--start-date",
        type=parse_date,
        default=None,
        help="수집 시작 날짜 (YYYY-MM-DD 형식, 기본값: 2017-01-01)",
    )
    
    parser.add_argument(
        "--end-date",
        type=parse_date,
        default=None,
        help="수집 종료 날짜 (YYYY-MM-DD 형식, 기본값: 현재 날짜)",
    )
    
    parser.add_argument(
        "--max-workers",
        type=int,
        default=2,
        help="병렬 처리 최대 워커 수 (기본값: 2, Rate limit 고려)",
    )
    
    args = parser.parse_args()
    
    setup_logging()
    logger = logging.getLogger(__name__)
    
    try:
        collector = CoinPricesCollector(max_workers=args.max_workers)
        
        if args.market_code:
            # 단일 코인 수집
            logger.info(f"단일 코인 수집 시작: {args.market_code}")
            result = collector.sync_single_coin_daily_candles(
                market_code=args.market_code,
                start_date=args.start_date,
                end_date=args.end_date,
            )
            logger.info(f"수집 완료: {result}")
        else:
            # 전체 코인 수집
            logger.info("전체 코인 수집 시작")
            summary = collector.sync_all_coins_daily_candles(
                start_date=args.start_date,
                end_date=args.end_date,
            )
            logger.info(f"수집 완료 요약: {summary}")
            
    except KeyboardInterrupt:
        logger.info("사용자에 의해 중단되었습니다")
        sys.exit(1)
    except Exception as e:
        logger.error(f"수집 중 에러 발생: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()

