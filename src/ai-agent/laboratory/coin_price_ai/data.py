"""코인 가격 데이터 로드 및 기간 추출.

CSV 경로는 모듈 기준으로 두어 추후 API로 교체 시 load_coin_price_data()만 수정하면 됩니다.
"""

from pathlib import Path

import pandas as pd


def get_csv_path() -> Path:
    """이 모듈과 같은 디렉터리의 CSV 경로 (추후 API로 교체 가능)."""
    return Path(__file__).parent / "coin_price_index.csv"


def load_coin_price_data(csv_path: Path | None = None) -> pd.DataFrame:
    """CSV에서 코인 가격 데이터를 로드하고 일자별 마지막 행으로 정리하여 반환."""
    csv_path = csv_path or get_csv_path()
    df = pd.read_csv(csv_path)
    df["open_time"] = pd.to_datetime(df["open_time"])
    df["date"] = df["open_time"].dt.normalize()
    use_cols = ["date", "open", "high", "low", "close", "price_change_pct"]
    df = df[use_cols].copy()
    df = df.groupby("date").last().reset_index()
    return df.sort_values("date").reset_index(drop=True)


def get_period_data(
    df: pd.DataFrame, target_date: str, months_before: int = 6
) -> str:
    """선택된 날짜 이전 N개월 ~ 선택된 날짜 구간의 '날짜: 시가|고가|저가|종가, 등락률' 텍스트를 반환."""
    target = pd.to_datetime(target_date)
    start = target - pd.DateOffset(months=months_before)
    end = target
    mask = (df["date"] >= start) & (df["date"] <= end)
    period = df.loc[
        mask, ["date", "open", "high", "low", "close", "price_change_pct"]
    ].copy()

    def fmt(r):
        d = r["date"].strftime("%Y-%m-%d")
        pct = r["price_change_pct"]
        pct_str = f"{pct:+.2%}" if pd.notna(pct) else "N/A"
        return f"{d}: {r['open']:.0f} | {r['high']:.0f} | {r['low']:.0f} | {r['close']:.0f}, {pct_str}"

    lines = period.apply(fmt, axis=1)
    return "\n".join(lines.tolist())
