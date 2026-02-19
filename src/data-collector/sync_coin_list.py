#!/usr/bin/env python3
"""
업비트 코인 목록 및 아이콘 최신화 스크립트

사용법:
    # 코인 목록과 아이콘 모두 최신화
    python sync_coin_list.py

    # 코인 목록만 최신화 (아이콘 다운로드 제외)
    python sync_coin_list.py --skip-images

    # 아이콘만 다운로드 (코인 목록은 이미 DB에 있는 경우)
    python sync_coin_list.py --images-only
"""
import argparse
import logging
import sys
import time
from pathlib import Path

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

# 모델 클래스 import
from model.Coins import Coins

# 서비스 및 유틸리티 import
from service.upbit_service import UpbitService
from utils.http_client import Http_client


def setup_logging():
    """로깅 설정"""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def download_coin_images(coin_list: list, image_dir: Path):
    """
    코인 아이콘 다운로드 (이미 있는 이미지는 건너뛰기)
    
    Args:
        coin_list: 코인 목록 (API 응답)
        image_dir: 이미지 저장 디렉토리
    """
    logger = logging.getLogger(__name__)
    
    # 이미지 디렉토리 생성
    image_dir.mkdir(parents=True, exist_ok=True)
    
    # 업비트 코인만 필터링
    upbit_coins = [
        coin for coin in coin_list 
        if coin.get("exchange") == "UPBIT"
    ]
    
    logger.info(f"아이콘 다운로드 시작: {len(upbit_coins)}개 코인")
    
    client = Http_client("https://static.upbit.com/logos/")
    downloaded_count = 0
    skipped_count = 0
    failed_count = 0
    
    for i, coin in enumerate(upbit_coins):
        symbol = coin.get("baseCurrencyCode")
        if not symbol:
            continue
        
        image_path = image_dir / f"{symbol}.png"
        
        # 이미 파일이 있으면 건너뛰기
        if image_path.exists():
            skipped_count += 1
            continue
        
        # Rate limit 고려 (5개마다 1초 대기)
        if downloaded_count > 0 and downloaded_count % 5 == 0:
            time.sleep(1)
        
        image_url = f"https://static.upbit.com/logos/{symbol}.png"
        
        if client.download_image(image_url, str(image_path)):
            downloaded_count += 1
        else:
            failed_count += 1
            logger.warning(f"아이콘 다운로드 실패: {symbol}")
    
    logger.info(
        f"아이콘 다운로드 완료: 새로 다운로드 {downloaded_count}개, "
        f"건너뛰기 {skipped_count}개, 실패 {failed_count}개"
    )


def main():
    parser = argparse.ArgumentParser(
        description="업비트 코인 목록 및 아이콘 최신화",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    
    parser.add_argument(
        "--skip-images",
        action="store_true",
        help="아이콘 다운로드 건너뛰기",
    )
    
    parser.add_argument(
        "--images-only",
        action="store_true",
        help="아이콘만 다운로드 (코인 목록은 DB에서 조회)",
    )
    
    parser.add_argument(
        "--image-dir",
        type=str,
        default="data/image",
        help="이미지 저장 디렉토리 (기본값: data/image)",
    )
    
    args = parser.parse_args()
    
    setup_logging()
    logger = logging.getLogger(__name__)
    
    try:
        # repository는 함수 내부에서 import (경로 문제 방지)
        from repository.coin_repository import CoinRepository
        
        upbit_service = UpbitService()
        coin_repository = CoinRepository()
        
        # 이미지만 다운로드하는 경우
        if args.images_only:
            logger.info("아이콘만 다운로드 모드")
            
            # DB에서 코인 목록 조회
            coins = coin_repository.get_all_coins()
            
            # API 응답 형식으로 변환
            coin_list = [
                {
                    "baseCurrencyCode": coin.symbol,
                    "exchange": coin.exchange,
                }
                for coin in coins
                if coin.exchange == "UPBIT"
            ]
            
            image_dir = Path(args.image_dir)
            download_coin_images(coin_list, image_dir)
            return
        
        # 코인 목록 가져오기
        logger.info("코인 목록 가져오기 시작...")
        fetched_data_list = upbit_service.fetch_all_coin_list()
        
        if not fetched_data_list:
            logger.error("코인 목록을 가져올 수 없습니다")
            sys.exit(1)
        
        logger.info(f"코인 목록 가져오기 완료: {len(fetched_data_list)}개")
        
        # 아이콘 다운로드
        if not args.skip_images:
            logger.info("아이콘 다운로드 시작...")
            image_dir = Path(args.image_dir)
            download_coin_images(fetched_data_list, image_dir)
        else:
            logger.info("아이콘 다운로드 건너뛰기")
        
        # market_code 형식 변환 함수
        def convert_market_code_format(market_code: str) -> str:
            """market_code 형식을 BTC/KRW → KRW-BTC로 변환"""
            if not market_code or "/" not in market_code:
                return market_code
            parts = market_code.split("/")
            if len(parts) == 2:
                return f"{parts[1]}-{parts[0]}"
            return market_code
        
        # DB에 저장할 코인 목록 생성
        logger.info("코인 목록 DB 저장 시작...")
        coin_list = [
            Coins(
                symbol=data.get("baseCurrencyCode"),
                quote_currency=data.get("quoteCurrencyCode"),
                market_code=convert_market_code_format(str(data.get("pair", ""))),
                korean_name=data.get("koreanName"),
                english_name=data.get("englishName"),
                img_url=f"/data/image/{data.get('baseCurrencyCode')}.png",
                exchange=data.get("exchange"),
                is_active=True,  # 명시적으로 True 설정
            )
            for data in fetched_data_list
            if data.get("exchange") == "UPBIT"
        ]
        
        result = coin_repository.save_coin_list(coin_list)
        logger.info(
            f"코인 목록 DB 저장 완료: 새로 추가 {result['new']}개, "
            f"건너뛰기 {result['skipped']}개, 총 {len(coin_list)}개"
        )
        
        logger.info("코인 목록 및 아이콘 최신화 완료!")
        
    except KeyboardInterrupt:
        logger.info("사용자에 의해 중단되었습니다")
        sys.exit(1)
    except Exception as e:
        logger.error(f"최신화 중 에러 발생: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()

