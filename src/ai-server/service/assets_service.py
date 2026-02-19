import logging
from typing import List, Dict, Any, Set, Tuple
from model.Assets import Assets
from dto.exchange_credentials_dto import ExchangeProvider


class AssetsService:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self._assets_repository = None
        self._coin_repository = None
        self._upbit_service = None
        self._exchange_credentials_service = None

    @property
    def assets_repository(self):
        if self._assets_repository is None:
            from repository.assets_repository import AssetsRepository

            self._assets_repository = AssetsRepository()
        return self._assets_repository

    @property
    def coin_repository(self):
        if self._coin_repository is None:
            from dependencies import get_coin_repository

            self._coin_repository = get_coin_repository()
        return self._coin_repository

    @property
    def upbit_service(self):
        if self._upbit_service is None:
            from dependencies import get_upbit_service

            self._upbit_service = get_upbit_service()
        return self._upbit_service

    @property
    def exchange_credentials_service(self):
        if self._exchange_credentials_service is None:
            from dependencies import get_exchange_credentials_service

            self._exchange_credentials_service = get_exchange_credentials_service()
        return self._exchange_credentials_service

    def _get_coin_id(self, symbol: str, trade_by_symbol: str) -> int | None:
        """symbol과 trade_by_symbol로 coin_id 조회"""
        try:
            coins = self.coin_repository.get_all_coins()

            # market_code 형식: BTC/KRW
            market_code = f"{symbol}/{trade_by_symbol}"

            for coin in coins:
                if coin.market_code == market_code:
                    return coin.id

            # market_code로 찾지 못하면 symbol과 quote_currency로 찾기
            for coin in coins:
                if coin.symbol == symbol and coin.quote_currency == trade_by_symbol:
                    return coin.id

            self.logger.warning(
                f"coin_id를 찾을 수 없습니다: symbol={symbol}, trade_by_symbol={trade_by_symbol}"
            )
            return None

        except Exception as e:
            self.logger.error(f"coin_id 조회 중 에러 발생: {e}")
            return None

    def _convert_upbit_account_to_asset(
        self, account: Dict[str, Any]
    ) -> Assets:
        """Upbit 계정 잔고 응답을 Assets 모델로 변환"""
        try:
            currency = account.get("currency", "")
            unit_currency = account.get("unit_currency", "KRW")
            balance = float(account.get("balance", "0"))
            locked = float(account.get("locked", "0"))
            avg_buy_price = float(account.get("avg_buy_price", "0"))
            avg_buy_price_modified = account.get("avg_buy_price_modified", False)

            # coin_id 조회
            coin_id = self._get_coin_id(currency, unit_currency)

            asset = Assets(
                coin_id=coin_id,
                symbol=currency,
                trade_by_symbol=unit_currency,
                quantity=balance,
                locked_quantity=locked,
                avg_buy_price=avg_buy_price,
                avg_buy_price_modified=avg_buy_price_modified,
            )

            return asset

        except Exception as e:
            self.logger.error(f"Upbit 계정 잔고 변환 중 에러 발생: {e}")
            raise e

    def sync_upbit_assets(self, user_id: str) -> Dict[str, Any]:
        """Upbit 잔고를 가져와서 assets 테이블에 동기화"""
        try:
            # 1. 자격증명 조회
            credentials = self.exchange_credentials_service.get_credentials(
                user_id, ExchangeProvider.UPBIT
            )

            if not credentials:
                raise ValueError("Upbit 자격증명을 찾을 수 없습니다")

            if not credentials.access_key or not credentials.secret_key:
                raise ValueError("자격증명 복호화에 실패했습니다")

            # 2. Upbit API로 계정 잔고 조회
            accounts = self.upbit_service.fetch_accounts(
                credentials.access_key, credentials.secret_key
            )

            if not accounts:
                self.logger.warning(f"Upbit 계정 잔고가 비어있습니다: user_id={user_id}")
                # 잔고가 없으면 모든 자산 삭제
                deleted_count = self.assets_repository.delete_assets_not_in_list(
                    user_id, ExchangeProvider.UPBIT.value, set()
                )
                return {
                    "saved_count": 0,
                    "deleted_count": deleted_count,
                    "assets": [],
                }

            # 3. Upbit 응답을 Assets 모델로 변환
            assets = []
            symbol_trade_by_pairs: Set[Tuple[str, str]] = set()

            for account in accounts:
                # 잔고가 0이고 locked도 0인 경우는 제외하지 않음 (보유 이력 유지)
                asset = self._convert_upbit_account_to_asset(account)
                assets.append(asset)
                symbol_trade_by_pairs.add((asset.symbol, asset.trade_by_symbol))

            # 4. 자산 저장/업데이트
            saved_assets = self.assets_repository.save_or_update_assets(
                user_id, ExchangeProvider.UPBIT.value, assets
            )

            # 5. 잔고에 없는 자산 삭제
            deleted_count = self.assets_repository.delete_assets_not_in_list(
                user_id, ExchangeProvider.UPBIT.value, symbol_trade_by_pairs
            )

            self.logger.info(
                f"Upbit 자산 동기화 완료: user_id={user_id}, saved={len(saved_assets)}, deleted={deleted_count}"
            )

            return {
                "saved_count": len(saved_assets),
                "deleted_count": deleted_count,
                "assets": [
                    {
                        "id": asset.id,
                        "symbol": asset.symbol,
                        "trade_by_symbol": asset.trade_by_symbol,
                        "quantity": float(asset.quantity),
                        "locked_quantity": float(asset.locked_quantity),
                        "avg_buy_price": float(asset.avg_buy_price),
                    }
                    for asset in saved_assets
                ],
            }

        except Exception as e:
            self.logger.error(f"Upbit 자산 동기화 중 에러 발생: {e}")
            raise e

