#!/usr/bin/env python3
"""
비활성 코인(is_active=false) 일봉 데이터 수집 및 활성화 스크립트

사용법:
    # 기본: 2017-01-01 ~ 현재
    python collect_inactive_coins.py

    # 특정 기간
    python collect_inactive_coins.py --start-date 2020-01-01 --end-date 2023-12-31
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
from database.database_connection import db
from model.Coins import Coins


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


def update_coin_active_status(coin_id: int, is_active: bool):
    """코인의 is_active 상태 업데이트"""
    session = None
    try:
        session = db.get_session()
        coin = session.query(Coins).filter(Coins.id == coin_id).first()
        if coin:
            coin.is_active = is_active
            session.commit()
            return True
        return False
    except Exception as e:
        logging.getLogger(__name__).error(f"코인 활성화 상태 업데이트 실패 (coin_id={coin_id}): {e}")
        if session:
            session.rollback()
        return False
    finally:
        if session:
            session.close()


def main():
    parser = argparse.ArgumentParser(
        description="비활성 코인 일봉 데이터 수집 및 활성화",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
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
        # 비활성 코인 목록 조회
        session = db.get_session()
        try:
            inactive_coins = session.query(Coins).filter(Coins.is_active == False).all()
            logger.info(f"비활성 코인 수: {len(inactive_coins)}")
        except Exception as e:
            logger.error(f"비활성 코인 목록 조회 실패: {e}")
            raise
        finally:
            session.close()
        
        if len(inactive_coins) == 0:
            logger.info("비활성 코인이 없습니다.")
            return
        
        collector = CoinPricesCollector(max_workers=args.max_workers)
        
        # 기본값 설정
        start_date = args.start_date
        if start_date is None:
            start_date = datetime(2017, 1, 1, tzinfo=pytz.UTC)
        end_date = args.end_date
        if end_date is None:
            end_date = datetime.now(pytz.UTC)
        
        logger.info(f"비활성 코인 일봉 데이터 수집 시작: {start_date} ~ {end_date}")
        
        # 각 코인별로 수집 및 활성화
        success_count = 0
        failed_count = 0
        activated_count = 0
        
        for coin in inactive_coins:
            logger.info(f"수집 시작: {coin.market_code} (coin_id={coin.id})")
            
            try:
                result = collector._fetch_and_save_candles(coin, start_date, end_date)
                
                # 수집 및 저장 성공 여부 확인
                if result.get("error") is None and result.get("total_saved", 0) > 0:
                    # 저장 성공 시 is_active를 true로 변경
                    if update_coin_active_status(coin.id, True):
                        logger.info(
                            f"✅ {coin.market_code}: 수집 성공 ({result['total_saved']}개 저장), "
                            f"활성화 완료"
                        )
                        activated_count += 1
                    else:
                        logger.warning(
                            f"⚠️ {coin.market_code}: 수집 성공했으나 활성화 실패"
                        )
                    success_count += 1
                else:
                    error_msg = result.get("error", "알 수 없는 에러")
                    logger.warning(
                        f"❌ {coin.market_code}: 수집 실패 - {error_msg}"
                    )
                    failed_count += 1
                    
            except Exception as e:
                logger.error(f"❌ {coin.market_code} 수집 중 예외 발생: {e}")
                failed_count += 1
        
        # 결과 요약
        logger.info("=" * 60)
        logger.info("수집 완료 요약")
        logger.info(f"전체 비활성 코인: {len(inactive_coins)}개")
        logger.info(f"수집 성공: {success_count}개")
        logger.info(f"수집 실패: {failed_count}개")
        logger.info(f"활성화 완료: {activated_count}개")
        logger.info("=" * 60)
            
    except KeyboardInterrupt:
        logger.info("사용자에 의해 중단되었습니다")
        sys.exit(1)
    except Exception as e:
        logger.error(f"수집 중 에러 발생: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()

