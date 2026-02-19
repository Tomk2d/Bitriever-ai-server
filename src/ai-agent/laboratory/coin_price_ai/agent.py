"""코인 가격 전문가 에이전트: 프롬프트, LLM, 체인 및 run()."""

from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

from langchain_core.prompts import load_prompt
from langchain_openai import ChatOpenAI

from .data import get_csv_path, get_period_data, load_coin_price_data
from .schemas import CoinPriceExpertResponse, parser

try:
    from langchain_teddynote import logging as langsmith_logging
    langsmith_logging.langsmith("coin-price-expert-agent")
except Exception:
    pass

_PROMPT_PATH = Path(__file__).parent / "prompts" / "coin_price_expert.yaml"
MODEL_NAME = "gpt-4.1"


def _get_chain():
    """프롬프트·LLM·파서로 체인 구성."""
    prompt = load_prompt(str(_PROMPT_PATH), encoding="utf-8")
    prompt = prompt.partial(format_instructions=parser.get_format_instructions())
    llm = ChatOpenAI(temperature=0, model=MODEL_NAME)
    return prompt | llm | parser


def run(
    target_date: str,
    months_before: int = 6,
    period_data: str | None = None,
) -> CoinPriceExpertResponse:
    """
    평가 일자에 대해 코인 가격 전문가 의견을 반환합니다.

    Args:
        target_date: 평가하고 싶은 일자 (예: "2019-02-19").
        months_before: 해당 일자 이전 몇 개월 데이터를 사용할지 (기본 6).
        period_data: 기간 데이터 문자열. 주어지면 사용(API 경로), None이면 CSV 로드(노트북용).

    Returns:
        CoinPriceExpertResponse
    """
    if period_data is None:
        df = load_coin_price_data(get_csv_path())
        period_data = get_period_data(df, target_date, months_before=months_before)
    chain = _get_chain()
    return chain.invoke(
        {
            "target_date": target_date,
            "period_data": period_data,
        }
    )
