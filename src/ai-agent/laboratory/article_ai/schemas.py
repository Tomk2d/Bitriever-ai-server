"""Pydantic 응답 스키마 및 OutputParser."""

from typing import Literal, List

from langchain_core.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field


class NotableArticleItem(BaseModel):
    """주목할 만한 기사 한 건: 날짜, 요약, 원문 URL."""

    date: str = Field(description="기사 날짜 (YYYY-MM-DD)")
    summary: str = Field(description="해당 기사 요약 또는 대표 헤드라인")
    original_url: str = Field(
        description="입력에 나온 기사의 URL. 주목할 기사로 선정 시 해당 URL을 그대로 출력"
    )


class NotablePeriod(BaseModel):
    title: str = Field(description="주목할 만한 이슈/기사 구간의 제목")
    period_text: str = Field(
        description="기간 문자열. 선택된 날짜 1일 + 이전 7일 (예: 2018-02-12 ~ 2018-02-19)"
    )
    period_data: List[NotableArticleItem] = Field(
        description=(
            "해당 기간의 주목할 만한 기사. 각 항목에 date, summary, original_url 포함. "
            "입력에 나온 기사의 URL을 선정 시 그대로 출력. 최대 7개."
        ),
        max_length=7,
    )


class ArticleExpertResponse(BaseModel):
    verdict: Literal["긍정적", "보통", "부정적"] = Field(
        description="해당 일자 매수/매도 판단에 대한 종합 의견 (반드시 세 값 중 하나)"
    )
    market_flow_analysis: str = Field(
        description="해당 기간 시장 흐름 분석: 헤드라인에서 읽힌 시장·규제·심리 등 흐름 설명"
    )
    short_long_term_perspective: str = Field(
        description="단기(해당 일 전후 뉴스 톤)와 장기(해당 8일 구간이 시사하는 바) 관점"
    )
    notable_periods: List[NotablePeriod] = Field(
        description="주목할 만한 이슈/기사 구간과 그 요약 (항목 최대 5개, 각 기간 최대 7일)"
    )


parser = PydanticOutputParser(pydantic_object=ArticleExpertResponse)
