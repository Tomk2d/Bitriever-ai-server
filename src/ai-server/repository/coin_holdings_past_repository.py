import logging
import uuid
from typing import List, Dict, Optional
from database.database_connection import db
from model.CoinHoldingsPast import CoinHoldingsPast


class CoinHoldingsPastRepository:
    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def save_or_update_holdings(
        self, user_id: str, exchange_code: int, holdings: Dict[int, Dict]
    ) -> List[CoinHoldingsPast]:
        """
        보유 종목 평단 저장/업데이트
        
        Args:
            user_id: 사용자 UUID
            exchange_code: 거래소 코드
            holdings: {coin_id: {"symbol": str, "avg_buy_price": Decimal, "remaining_quantity": Decimal}}
        
        Returns:
            저장/업데이트된 보유 종목 목록
        """
        try:
            session = db.get_session()

            # user_id를 UUID로 변환
            user_uuid = uuid.UUID(user_id) if isinstance(user_id, str) else user_id

            saved_holdings = []

            for coin_id, holding_data in holdings.items():
                # 기존 보유 종목 확인
                existing = (
                    session.query(CoinHoldingsPast)
                    .filter(
                        CoinHoldingsPast.user_id == user_uuid,
                        CoinHoldingsPast.coin_id == coin_id,
                        CoinHoldingsPast.exchange_code == exchange_code,
                    )
                    .first()
                )

                if existing:
                    # 기존 보유 종목 업데이트
                    existing.avg_buy_price = holding_data["avg_buy_price"]
                    existing.remaining_quantity = holding_data["remaining_quantity"]
                    existing.symbol = holding_data["symbol"]
                    # updated_at은 DB 트리거로 자동 업데이트됨
                    saved_holdings.append(existing)
                else:
                    # 새로운 보유 종목 저장
                    new_holding = CoinHoldingsPast(
                        user_id=user_uuid,
                        coin_id=coin_id,
                        exchange_code=exchange_code,
                        symbol=holding_data["symbol"],
                        avg_buy_price=holding_data["avg_buy_price"],
                        remaining_quantity=holding_data["remaining_quantity"],
                    )
                    session.add(new_holding)
                    saved_holdings.append(new_holding)

            session.commit()

            for holding in saved_holdings:
                session.refresh(holding)

            self.logger.info(
                f"보유 종목 평단 저장/업데이트 완료: user_id={user_id}, exchange_code={exchange_code}, count={len(saved_holdings)}"
            )
            return saved_holdings

        except Exception as e:
            self.logger.error(f"보유 종목 평단 저장/업데이트 중 에러 발생: {e}")
            session.rollback()
            raise e
        finally:
            session.close()

    def delete_holdings_not_in_list(
        self, user_id: str, exchange_code: int, coin_ids: set
    ) -> int:
        """
        특정 코인 목록에 없는 보유 종목 삭제
        
        Args:
            user_id: 사용자 UUID
            exchange_code: 거래소 코드
            coin_ids: 유지할 coin_id 집합
        
        Returns:
            삭제된 보유 종목 수
        """
        try:
            session = db.get_session()

            # user_id를 UUID로 변환
            user_uuid = uuid.UUID(user_id) if isinstance(user_id, str) else user_id

            # 해당 사용자의 해당 거래소의 모든 보유 종목 조회
            all_holdings = (
                session.query(CoinHoldingsPast)
                .filter(
                    CoinHoldingsPast.user_id == user_uuid,
                    CoinHoldingsPast.exchange_code == exchange_code,
                )
                .all()
            )

            # 삭제할 보유 종목 목록 생성
            holdings_to_delete = []
            for holding in all_holdings:
                if holding.coin_id not in coin_ids:
                    holdings_to_delete.append(holding)

            # 삭제 실행
            deleted_count = 0
            for holding in holdings_to_delete:
                session.delete(holding)
                deleted_count += 1

            session.commit()

            self.logger.info(
                f"보유 종목 평단 삭제 완료: user_id={user_id}, exchange_code={exchange_code}, count={deleted_count}"
            )
            return deleted_count

        except Exception as e:
            self.logger.error(f"보유 종목 평단 삭제 중 에러 발생: {e}")
            session.rollback()
            raise e
        finally:
            session.close()

    def find_by_user_and_exchange(
        self, user_id: str, exchange_code: int
    ) -> List[CoinHoldingsPast]:
        """
        사용자와 거래소별 보유 종목 조회
        
        Args:
            user_id: 사용자 UUID
            exchange_code: 거래소 코드
        
        Returns:
            보유 종목 목록
        """
        try:
            session = db.get_session()

            # user_id를 UUID로 변환
            user_uuid = uuid.UUID(user_id) if isinstance(user_id, str) else user_id

            holdings = (
                session.query(CoinHoldingsPast)
                .filter(
                    CoinHoldingsPast.user_id == user_uuid,
                    CoinHoldingsPast.exchange_code == exchange_code,
                )
                .all()
            )
            return holdings
        except Exception as e:
            self.logger.error(f"보유 종목 평단 조회 중 에러 발생: {e}")
            raise e
        finally:
            session.close()

    def get_holdings_dict(
        self, user_id: str, exchange_code: int
    ) -> Dict[int, Dict]:
        """
        사용자와 거래소별 보유 종목을 딕셔너리로 조회
        
        Args:
            user_id: 사용자 UUID
            exchange_code: 거래소 코드
        
        Returns:
            {coin_id: {"avg_buy_price": Decimal, "remaining_quantity": Decimal, "symbol": str}}
        """
        try:
            holdings = self.find_by_user_and_exchange(user_id, exchange_code)
            holdings_dict = {}
            for holding in holdings:
                holdings_dict[holding.coin_id] = {
                    "avg_buy_price": holding.avg_buy_price,
                    "remaining_quantity": holding.remaining_quantity,
                    "symbol": holding.symbol,
                }
            return holdings_dict
        except Exception as e:
            self.logger.error(f"보유 종목 평단 딕셔너리 조회 중 에러 발생: {e}")
            raise e

