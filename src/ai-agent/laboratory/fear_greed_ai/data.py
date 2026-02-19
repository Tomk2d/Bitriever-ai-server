"""공포/탐욕 지수 데이터 로드 및 기간 추출.

CSV 경로는 모듈 기준으로 두어 추후 API로 교체 시 load_fear_greed_data()만 수정하면 됩니다.
"""

from pathlib import Path

import pandas as pd


def get_csv_path() -> Path:
    """이 모듈과 같은 디렉터리의 CSV 경로 (추후 API로 교체 가능)."""
    return Path(__file__).parent / "fear_greed_index.csv"


def load_fear_greed_data(csv_path: Path | None = None) -> pd.DataFrame:
    """CSV에서 공포/탐욕 지수 데이터를 로드하고 날짜순 정렬하여 반환."""
    csv_path = csv_path or get_csv_path()
    df = pd.read_csv(csv_path)
    df["date"] = pd.to_datetime(df["date"])
    return df.sort_values("date").reset_index(drop=True)


def get_period_data(
    df: pd.DataFrame, target_date: str, months_before: int = 6
) -> str:
    """선택된 날짜 이전 N개월 ~ 선택된 날짜 구간의 '날짜: 지수' 텍스트를 반환."""
    target = pd.to_datetime(target_date)
    start = target - pd.DateOffset(months=months_before)
    end = target
    mask = (df["date"] >= start) & (df["date"] <= end)
    period = df.loc[mask, ["date", "fear_greed_index"]]
    lines = period.apply(
        lambda r: f"{r['date'].strftime('%Y-%m-%d')}: {r['fear_greed_index']}",
        axis=1,
    )
    return "\n".join(lines.tolist())
