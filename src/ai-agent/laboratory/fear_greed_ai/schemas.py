"""Pydantic 응답 스키마 및 OutputParser."""

from typing import Literal, List, Dict

from langchain_core.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field


# 과거 주목 기간 한 항목 (선택되는 기간은 최대 7일로 제한)
class NotablePeriod(BaseModel):
    title: str = Field(
        description="기간의 제목 (예: 공포에서 탐욕으로의 급격한 전환)"
    )
    period_text: str = Field(
        description="기간 문자열. 반드시 최대 7일 이내 (예: 2019-02-17 ~ 2019-02-19)"
    )
    period_data: List[Dict[str, int]] = Field(
        description=(
            '각 날짜별 지수. 최대 7개 항목(최대 7일). '
            '각 항목은 하나의 날짜(키)와 지수(값) 객체. '
            '예: [{"2019-02-17": 38}, {"2019-02-18": 63}, {"2019-02-19": 65}]'
        ),
        max_length=7,
    )


# 전문가 에이전트 최종 응답
class FearGreedExpertResponse(BaseModel):
    verdict: Literal["긍정적", "보통", "부정적"] = Field(
        description="해당 일자 매수/매도 판단에 대한 종합 의견 (반드시 세 값 중 하나)"
    )
    market_flow_analysis: str = Field(
        description="해당 기간 시장 흐름 분석: 공포/탐욕 지수 추이와 국면 설명"
    )
    short_long_term_perspective: str = Field(
        description=(
            "단기적 관점과 장기적 관점을 각각 서술 "
            "(예: 단기: 해당 일자 전후 심리·추이, 장기: 6개월 구간에서의 위치·추세)"
        )
    )
    notable_periods: List[NotablePeriod] = Field(
        description="과거 데이터에서 주목할 만한 기간과 그 수치 (항목 최대 5개, 각 기간은 최대 7일)"
    )


parser = PydanticOutputParser(pydantic_object=FearGreedExpertResponse)
