#!/usr/bin/env python3
"""
특정 코인 가격 데이터 수집 테스트 스크립트

사용법:
    # 기본 (KRW-BTC, 2017-01-01 ~ 현재)
    python test_single_coin.py

    # 다른 코인 테스트
    python test_single_coin.py --market-code KRW-ETH

    # 특정 기간만 테스트
    python test_single_coin.py --start-date 2024-01-01
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

# SQLAlchemy 관계를 위해 모든 모델을 명시적으로 import
import model.Users
import model.ExchangeCredentials
import model.Coins
import model.TradingHistories
import model.Assets
import model.CoinHoldingsPast
import model.CoinPricesDay

# data-collector 모듈 import (같은 디렉토리이므로 직접 import)
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
        description="특정 코인 가격 데이터 수집 테스트",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    
    parser.add_argument(
        "--market-code",
        type=str,
        default="KRW-BTC",
        help="거래쌍 코드 (기본값: KRW-BTC)",
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
    
    args = parser.parse_args()
    
    setup_logging()
    logger = logging.getLogger(__name__)
    
    logger.info("=" * 60)
    logger.info("특정 코인 가격 데이터 수집 테스트 시작")
    logger.info(f"코인: {args.market_code}")
    logger.info("=" * 60)
    
    try:
        collector = CoinPricesCollector(max_workers=1)  # 테스트는 단일 워커로
        
        result = collector.sync_single_coin_daily_candles(
            market_code=args.market_code,
            start_date=args.start_date,
            end_date=args.end_date,
        )
        
        logger.info("=" * 60)
        logger.info("테스트 완료!")
        logger.info(f"코인: {result['market_code']}")
        logger.info(f"수집된 캔들: {result['total_fetched']}개")
        logger.info(f"저장된 캔들: {result['total_saved']}개")
        if result.get("error"):
            logger.warning(f"에러: {result['error']}")
        logger.info("=" * 60)
        
    except KeyboardInterrupt:
        logger.info("사용자에 의해 중단되었습니다")
        sys.exit(1)
    except Exception as e:
        logger.error(f"테스트 중 에러 발생: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()

