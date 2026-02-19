"""매매 분석·평가 메타 에이전트 응답 스키마 및 Parser."""

from langchain_core.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field


class TradeEvaluationExpertResponse(BaseModel):
    """메타 에이전트의 매매 분석·평가 응답."""

    article_expert_evaluation: str = Field(
        description="기사 전문가 의견에 대한 평가 (해당 의견의 타당성, 매매와의 관계 등)"
    )
    coin_price_expert_evaluation: str = Field(
        description="코인가격 전문가 의견에 대한 평가 (해당 의견의 타당성, 매매와의 관계 등)"
    )
    fear_greed_expert_evaluation: str = Field(
        description="공포/탐욕 전문가 의견에 대한 평가 (해당 의견의 타당성, 매매와의 관계 등)"
    )
    own_trade_analysis: str = Field(
        description="본인(이 에이전트)의 유저 매매에 대한 분석 및 평가 (타이밍, 손익, 의도 반영 여부 등)"
    )
    suggestions: str = Field(
        description="다음 매매나 습관에 대한 구체적 제안/권고"
    )


parser = PydanticOutputParser(pydantic_object=TradeEvaluationExpertResponse)
