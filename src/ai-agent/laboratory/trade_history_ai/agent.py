"""매매 분석·평가 메타 에이전트: 프롬프트, LLM, 체인 및 run()."""

from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

from langchain_core.prompts import load_prompt
from langchain_openai import ChatOpenAI

from .schemas import TradeEvaluationExpertResponse, parser

try:
    from langchain_teddynote import logging as langsmith_logging
    langsmith_logging.langsmith("trade-evaluation-expert-agent")
except Exception:
    pass

_PROMPT_PATH = Path(__file__).parent / "prompts" / "trade_evaluation_expert.yaml"
MODEL_NAME = "gpt-4.1"


def _get_chain():
    """프롬프트·LLM·파서로 체인 구성."""
    prompt = load_prompt(str(_PROMPT_PATH), encoding="utf-8")
    prompt = prompt.partial(format_instructions=parser.get_format_instructions())
    llm = ChatOpenAI(temperature=0, model=MODEL_NAME)
    return prompt | llm | parser


def run(
    target_period: str,
    expert_article_summary: str,
    expert_coin_price_summary: str,
    expert_fear_greed_summary: str,
    trade_history_text: str,
    diary_trading_mind: str = "",
    diary_reason: str = "",
) -> TradeEvaluationExpertResponse:
    """
    세 전문가 요약과 매매 내역 텍스트, 매매 일지(투자 심리·투자 근거)를 받아 매매 분석·평가를 반환합니다.

    노트북: 전문가 요약·매매 텍스트·diary_trading_mind·diary_reason을 하드코딩으로 넘기면 됨.
    API: 서비스에서 3 에이전트 호출 + DB 매매·일지 조회 후 run() 호출.

    Args:
        target_period: 시장 의견 기준일 (예: "2019-02-19").
        expert_article_summary: 기사 전문가 의견 요약.
        expert_coin_price_summary: 코인가격 전문가 의견 요약.
        expert_fear_greed_summary: 공포/탐욕 전문가 의견 요약.
        trade_history_text: 포맷된 매매 내역 한 줄 문자열.
        diary_trading_mind: 매매 일지의 투자 심리 한글 (예: 무념무상, 확신, 두려움).
        diary_reason: 매매 일지의 투자 근거/내용 (content의 type=text 블록 문자열).

    Returns:
        TradeEvaluationExpertResponse.
    """
    chain = _get_chain()
    return chain.invoke(
        {
            "target_period": target_period,
            "expert_article_summary": expert_article_summary,
            "expert_coin_price_summary": expert_coin_price_summary,
            "expert_fear_greed_summary": expert_fear_greed_summary,
            "diary_trading_mind": diary_trading_mind or "(미기입)",
            "diary_reason": diary_reason or "(매매 일지 없음)",
            "trade_history_text": trade_history_text,
        }
    )
