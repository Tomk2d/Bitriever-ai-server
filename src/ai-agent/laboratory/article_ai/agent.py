"""기사(헤드라인) 전문가 에이전트: 프롬프트, LLM, 체인 및 run()."""

from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

from langchain_core.prompts import load_prompt
from langchain_openai import ChatOpenAI

from .data import (
    MAX_HEADLINES_PER_DAY,
    get_csv_path,
    get_period_data,
    load_article_data,
)
from .schemas import ArticleExpertResponse, parser

try:
    from langchain_teddynote import logging as langsmith_logging
    langsmith_logging.langsmith("article-expert-agent")
except Exception:
    pass

_PROMPT_PATH = Path(__file__).parent / "prompts" / "article_expert.yaml"
MODEL_NAME = "gpt-4.1"


def _get_chain():
    """프롬프트·LLM·파서로 체인 구성."""
    prompt = load_prompt(str(_PROMPT_PATH), encoding="utf-8")
    prompt = prompt.partial(format_instructions=parser.get_format_instructions())
    llm = ChatOpenAI(temperature=0, model=MODEL_NAME)
    return prompt | llm | parser


def run(
    target_date: str,
    days_before: int = 7,
    max_headlines_per_day: int = MAX_HEADLINES_PER_DAY,
    period_data: str | None = None,
) -> ArticleExpertResponse:
    """
    평가 일자에 대해 기사 헤드라인 기반 시장 분위기·이슈 의견을 반환합니다.

    Args:
        target_date: 평가하고 싶은 일자 (예: "2019-02-19").
        days_before: 선택일 포함 과거 며칠까지 사용할지 (기본 7 → 총 8일).
        max_headlines_per_day: 일자당 최대 헤드라인 개수 (기본 30).
        period_data: 기간 데이터 문자열. 주어지면 사용(API 경로), None이면 CSV 로드(노트북용).

    Returns:
        ArticleExpertResponse
    """
    if period_data is None:
        df = load_article_data(get_csv_path())
        period_data = get_period_data(
            df,
            target_date,
            days_before=days_before,
            max_headlines_per_day=max_headlines_per_day,
        )
    chain = _get_chain()
    return chain.invoke(
        {
            "target_date": target_date,
            "period_data": period_data,
        }
    )
