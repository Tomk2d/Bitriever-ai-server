from fastapi import Depends
from typing import Annotated, Any
from repository.coin_repository import CoinRepository
from repository.user_repository import UserRepository

# 싱글톤 인스턴스들
_upbit_service_instance = None
_coin_service_instance = None
_coin_repository_instance = None
_user_service_instance = None
_user_repository_instance = None
_trading_histories_service_instance = None
_exchange_credentials_service_instance = None
_assets_service_instance = None
_trading_profit_service_instance = None
_fear_greed_agent_service_instance = None
_coin_price_agent_service_instance = None
_article_agent_service_instance = None
_fear_greed_index_repository_instance = None
_coin_price_day_repository_instance = None
_article_repository_instance = None
_trading_histories_repository_instance = None
_trade_evaluation_agent_service_instance = None
_diary_repository_instance = None
_trade_evaluation_result_repository_instance = None


# 의존성 주입 함수들
def get_user_service() -> Any:
    global _user_service_instance
    if _user_service_instance is None:
        from service.user_service import UserService  # lazy import

        _user_service_instance = UserService()
    return _user_service_instance


def get_user_repository() -> UserRepository:
    global _user_repository_instance
    if _user_repository_instance is None:
        _user_repository_instance = UserRepository()
    return _user_repository_instance


def get_upbit_service() -> Any:  # Any로 타입 힌트
    global _upbit_service_instance
    if _upbit_service_instance is None:
        from service.upbit_service import UpbitService  # lazy import

        _upbit_service_instance = UpbitService()
    return _upbit_service_instance


def get_coin_service() -> Any:  # Any로 타입 힌트
    global _coin_service_instance
    if _coin_service_instance is None:
        from service.coin_service import CoinService  # lazy import

        _coin_service_instance = CoinService()
    return _coin_service_instance


def get_coin_repository() -> CoinRepository:
    global _coin_repository_instance
    if _coin_repository_instance is None:
        _coin_repository_instance = CoinRepository()
    return _coin_repository_instance


def get_trading_histories_service() -> Any:
    global _trading_histories_service_instance
    if _trading_histories_service_instance is None:
        from service.trading_histories_service import TradingHistoriesService

        _trading_histories_service_instance = TradingHistoriesService()
    return _trading_histories_service_instance


def get_exchange_credentials_service() -> Any:
    global _exchange_credentials_service_instance
    if _exchange_credentials_service_instance is None:
        from service.exchange_credentials_service import ExchangeCredentialsService

        _exchange_credentials_service_instance = ExchangeCredentialsService()
    return _exchange_credentials_service_instance


def get_assets_service() -> Any:
    global _assets_service_instance
    if _assets_service_instance is None:
        from service.assets_service import AssetsService

        _assets_service_instance = AssetsService()
    return _assets_service_instance


def get_trading_profit_service() -> Any:
    global _trading_profit_service_instance
    if _trading_profit_service_instance is None:
        from service.trading_profit_service import TradingProfitService

        _trading_profit_service_instance = TradingProfitService()
    return _trading_profit_service_instance


def get_fear_greed_index_repository() -> Any:
    global _fear_greed_index_repository_instance
    if _fear_greed_index_repository_instance is None:
        from repository.fear_greed_index_repository import FearGreedIndexRepository

        _fear_greed_index_repository_instance = FearGreedIndexRepository()
    return _fear_greed_index_repository_instance


def get_coin_price_day_repository() -> Any:
    global _coin_price_day_repository_instance
    if _coin_price_day_repository_instance is None:
        from repository.coin_price_day_repository import CoinPriceDayRepository

        _coin_price_day_repository_instance = CoinPriceDayRepository()
    return _coin_price_day_repository_instance


def get_article_repository() -> Any:
    global _article_repository_instance
    if _article_repository_instance is None:
        from repository.article_repository import ArticleRepository

        _article_repository_instance = ArticleRepository()
    return _article_repository_instance


def get_fear_greed_agent_service() -> Any:
    global _fear_greed_agent_service_instance
    if _fear_greed_agent_service_instance is None:
        from service.fear_greed_agent_service import FearGreedAgentService

        _fear_greed_agent_service_instance = FearGreedAgentService(
            get_fear_greed_index_repository()
        )
    return _fear_greed_agent_service_instance


def get_coin_price_agent_service() -> Any:
    global _coin_price_agent_service_instance
    if _coin_price_agent_service_instance is None:
        from service.coin_price_agent_service import CoinPriceAgentService

        _coin_price_agent_service_instance = CoinPriceAgentService(
            get_coin_price_day_repository()
        )
    return _coin_price_agent_service_instance


def get_article_agent_service() -> Any:
    global _article_agent_service_instance
    if _article_agent_service_instance is None:
        from service.article_agent_service import ArticleAgentService

        _article_agent_service_instance = ArticleAgentService(get_article_repository())
    return _article_agent_service_instance


def get_trading_histories_repository() -> Any:
    global _trading_histories_repository_instance
    if _trading_histories_repository_instance is None:
        from repository.trading_histories_repository import TradingHistoriesRepository

        _trading_histories_repository_instance = TradingHistoriesRepository()
    return _trading_histories_repository_instance


def get_diary_repository() -> Any:
    global _diary_repository_instance
    if _diary_repository_instance is None:
        from repository.diary_repository import DiaryRepository

        _diary_repository_instance = DiaryRepository()
    return _diary_repository_instance


def get_trade_evaluation_agent_service() -> Any:
    global _trade_evaluation_agent_service_instance
    if _trade_evaluation_agent_service_instance is None:
        from service.trade_evaluation_agent_service import TradeEvaluationAgentService

        _trade_evaluation_agent_service_instance = TradeEvaluationAgentService(
            get_article_agent_service(),
            get_coin_price_agent_service(),
            get_fear_greed_agent_service(),
            get_trading_histories_repository(),
            get_diary_repository(),
        )
    return _trade_evaluation_agent_service_instance


def get_trade_evaluation_result_repository() -> Any:
    global _trade_evaluation_result_repository_instance
    if _trade_evaluation_result_repository_instance is None:
        from repository.trade_evaluation_result_repository import (
            TradeEvaluationResultRepository,
        )

        _trade_evaluation_result_repository_instance = TradeEvaluationResultRepository()
    return _trade_evaluation_result_repository_instance
