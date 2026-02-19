import logging
import uuid
from typing import List, Set, Tuple
from database.database_connection import db
from model.Assets import Assets


class AssetsRepository:
    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def save_or_update_assets(
        self, user_id: str, exchange_code: int, assets: List[Assets]
    ) -> List[Assets]:
        """자산 목록 저장/업데이트"""
        try:
            session = db.get_session()

            # user_id를 UUID로 변환
            user_uuid = uuid.UUID(user_id) if isinstance(user_id, str) else user_id

            saved_assets = []

            for asset in assets:
                # 기존 자산 확인 (user_id, exchange_code, symbol, trade_by_symbol)
                existing = (
                    session.query(Assets)
                    .filter(
                        Assets.user_id == user_uuid,
                        Assets.exchange_code == exchange_code,
                        Assets.symbol == asset.symbol,
                        Assets.trade_by_symbol == asset.trade_by_symbol,
                    )
                    .first()
                )

                if existing:
                    # 기존 자산 업데이트
                    existing.quantity = asset.quantity
                    existing.locked_quantity = asset.locked_quantity
                    existing.avg_buy_price = asset.avg_buy_price
                    existing.avg_buy_price_modified = asset.avg_buy_price_modified
                    existing.coin_id = asset.coin_id
                    # updated_at은 DB 트리거로 자동 업데이트됨
                    saved_assets.append(existing)
                else:
                    # 새로운 자산 저장
                    asset.user_id = user_uuid
                    asset.exchange_code = exchange_code
                    session.add(asset)
                    saved_assets.append(asset)

            session.commit()

            for asset in saved_assets:
                session.refresh(asset)

            self.logger.info(
                f"자산 저장/업데이트 완료: user_id={user_id}, exchange_code={exchange_code}, count={len(saved_assets)}"
            )
            return saved_assets

        except Exception as e:
            self.logger.error(f"자산 저장/업데이트 중 에러 발생: {e}")
            session.rollback()
            raise e
        finally:
            session.close()

    def delete_assets_not_in_list(
        self, user_id: str, exchange_code: int, symbol_trade_by_pairs: Set[Tuple[str, str]]
    ) -> int:
        """특정 자산 목록에 없는 자산 삭제"""
        try:
            session = db.get_session()

            # user_id를 UUID로 변환
            user_uuid = uuid.UUID(user_id) if isinstance(user_id, str) else user_id

            # 해당 사용자의 해당 거래소의 모든 자산 조회
            all_assets = (
                session.query(Assets)
                .filter(
                    Assets.user_id == user_uuid,
                    Assets.exchange_code == exchange_code,
                )
                .all()
            )

            # 삭제할 자산 목록 생성
            assets_to_delete = []
            for asset in all_assets:
                pair = (asset.symbol, asset.trade_by_symbol)
                if pair not in symbol_trade_by_pairs:
                    assets_to_delete.append(asset)

            # 삭제 실행
            deleted_count = 0
            for asset in assets_to_delete:
                session.delete(asset)
                deleted_count += 1

            session.commit()

            self.logger.info(
                f"자산 삭제 완료: user_id={user_id}, exchange_code={exchange_code}, count={deleted_count}"
            )
            return deleted_count

        except Exception as e:
            self.logger.error(f"자산 삭제 중 에러 발생: {e}")
            session.rollback()
            raise e
        finally:
            session.close()

    def find_by_user_and_exchange(
        self, user_id: str, exchange_code: int
    ) -> List[Assets]:
        """사용자와 거래소별 자산 조회"""
        try:
            session = db.get_session()

            # user_id를 UUID로 변환
            user_uuid = uuid.UUID(user_id) if isinstance(user_id, str) else user_id

            assets = (
                session.query(Assets)
                .filter(
                    Assets.user_id == user_uuid,
                    Assets.exchange_code == exchange_code,
                )
                .all()
            )
            return assets
        except Exception as e:
            self.logger.error(f"자산 조회 중 에러 발생: {e}")
            raise e
        finally:
            session.close()

