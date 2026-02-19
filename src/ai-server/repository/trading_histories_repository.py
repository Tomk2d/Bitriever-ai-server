import logging
from typing import List, Optional
from database.database_connection import db
from model.TradingHistories import TradingHistories


class TradingHistoriesRepository:
    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def save_trading_histories(
        self, trading_histories: List[TradingHistories]
    ) -> List[TradingHistories]:
        """거래내역 목록 저장"""
        try:
            session = db.get_session()

            # 기존 거래내역과 중복 체크 (trade_uuid 기준)
            saved_histories = []

            for history in trading_histories:
                # 기존 거래내역 확인
                existing = (
                    session.query(TradingHistories)
                    .filter(
                        TradingHistories.user_id == history.user_id,
                        TradingHistories.exchange_code == history.exchange_code,
                        TradingHistories.trade_uuid == history.trade_uuid,
                    )
                    .first()
                )

                if existing:
                    continue

                session.add(history)
                saved_histories.append(history)

            session.commit()

            for history in saved_histories:
                session.refresh(history)

            self.logger.info(f"거래내역 저장 완료: {len(saved_histories)}개")
            return saved_histories

        except Exception as e:
            self.logger.error(f"거래내역 저장 중 에러 발생: {e}")
            session.rollback()
            raise e
        finally:
            session.close()

    def find_by_user_and_exchange(
        self, user_id: str, exchange_code: int
    ) -> List[TradingHistories]:
        """사용자와 거래소별 거래내역 조회"""
        try:
            session = db.get_session()
            histories = (
                session.query(TradingHistories)
                .filter(
                    TradingHistories.user_id == user_id,
                    TradingHistories.exchange_code == exchange_code,
                )
                .order_by(TradingHistories.trade_time.desc())
                .all()
            )
            return histories
        except Exception as e:
            self.logger.error(f"거래내역 조회 중 에러 발생: {e}")
            raise e
        finally:
            session.close()

    def find_by_user_id(self, user_id: str) -> List[TradingHistories]:
        """사용자 ID로 모든 거래내역 조회"""
        try:
            session = db.get_session()
            histories = (
                session.query(TradingHistories)
                .filter(TradingHistories.user_id == user_id)
                .order_by(TradingHistories.trade_time.desc())
                .all()
            )
            return histories
        except Exception as e:
            self.logger.error(f"사용자 거래내역 조회 중 에러 발생: {e}")
            raise e
        finally:
            session.close()

    def find_by_user_id_and_trade_time_between(
        self,
        session,
        user_id: str,
        start_dt,
        end_dt,
    ) -> List[TradingHistories]:
        """사용자 ID와 trade_time 구간으로 거래내역 조회. trade_time 오름차순(과거→최신)."""
        return (
            session.query(TradingHistories)
            .filter(
                TradingHistories.user_id == user_id,
                TradingHistories.trade_time >= start_dt,
                TradingHistories.trade_time < end_dt,
            )
            .order_by(TradingHistories.trade_time.asc())
            .all()
        )

    def find_by_user_id_and_id(
        self, session, user_id: str, trade_id: int
    ) -> Optional[TradingHistories]:
        """사용자 ID와 거래 내역 ID로 단일 거래 조회. 없으면 None."""
        return (
            session.query(TradingHistories)
            .filter(
                TradingHistories.user_id == user_id,
                TradingHistories.id == trade_id,
            )
            .first()
        )

    def delete_by_user_and_exchange(self, user_id: str, exchange_code: int) -> bool:
        """사용자와 거래소별 거래내역 삭제"""
        try:
            session = db.get_session()
            deleted_count = (
                session.query(TradingHistories)
                .filter(
                    TradingHistories.user_id == user_id,
                    TradingHistories.exchange_code == exchange_code,
                )
                .delete()
            )
            session.commit()

            self.logger.info(f"거래내역 삭제 완료: {deleted_count}개")
            return True
        except Exception as e:
            self.logger.error(f"거래내역 삭제 중 에러 발생: {e}")
            session.rollback()
            raise e
        finally:
            session.close()

    def update_profit_loss(
        self, trading_histories: List[TradingHistories]
    ) -> List[TradingHistories]:
        """
        거래내역의 수익률 및 평균 구매 단가 업데이트
        
        Args:
            trading_histories: 업데이트할 거래내역 목록
        
        Returns:
            업데이트된 거래내역 목록
        """
        try:
            session = db.get_session()

            updated_histories = []

            for history in trading_histories:
                # 기존 거래내역 확인
                existing = (
                    session.query(TradingHistories)
                    .filter(TradingHistories.id == history.id)
                    .first()
                )

                if existing:
                    # 수익률 및 평균 구매 단가 업데이트
                    existing.profit_loss_rate = history.profit_loss_rate
                    existing.avg_buy_price = history.avg_buy_price
                    updated_histories.append(existing)

            session.commit()

            for history in updated_histories:
                session.refresh(history)

            self.logger.info(f"거래내역 수익률 업데이트 완료: {len(updated_histories)}개")
            return updated_histories

        except Exception as e:
            self.logger.error(f"거래내역 수익률 업데이트 중 에러 발생: {e}")
            session.rollback()
            raise e
        finally:
            session.close()
