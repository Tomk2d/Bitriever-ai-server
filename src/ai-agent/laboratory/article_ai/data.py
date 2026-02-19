"""기사 헤드라인 데이터 로드 및 기간 추출.

CSV 경로는 모듈 기준으로 두어 추후 API로 교체 시 load_article_data()만 수정하면 됩니다.
"""

from pathlib import Path

import pandas as pd

MAX_HEADLINES_PER_DAY = 30


def get_csv_path() -> Path:
    """이 모듈과 같은 디렉터리의 CSV 경로 (추후 API로 교체 가능)."""
    return Path(__file__).parent / "article_headline.csv"


def load_article_data(csv_path: Path | None = None) -> pd.DataFrame:
    """CSV에서 기사 헤드라인 데이터를 로드하여 반환."""
    csv_path = csv_path or get_csv_path()
    df = pd.read_csv(csv_path)
    df.columns = df.columns.str.strip()
    df["published_at"] = pd.to_datetime(df["published_at"])
    df["date"] = df["published_at"].dt.normalize()
    return df.sort_values(["date", "published_at"]).reset_index(drop=True)


def get_period_data(
    df: pd.DataFrame,
    target_date: str,
    days_before: int = 7,
    max_headlines_per_day: int = MAX_HEADLINES_PER_DAY,
) -> str:
    """선택일 포함, 선택일 기준 과거 days_before일까지의 헤드라인을 일자별로 묶어 반환."""
    target = pd.to_datetime(target_date).normalize()
    start = target - pd.Timedelta(days=days_before)
    end = target
    mask = (df["date"] >= start) & (df["date"] <= end)
    period = df.loc[mask, ["date", "headline", "published_at"]].copy()
    lines = []
    for d, g in period.groupby("date", sort=True):
        g = g.sort_values("published_at", ascending=False).head(max_headlines_per_day)
        headlines = g["headline"].astype(str).str.strip().tolist()
        day_str = pd.Timestamp(d).strftime("%Y-%m-%d")
        lines.append(day_str + ": " + " | ".join(headlines))
    return "\n".join(lines)
