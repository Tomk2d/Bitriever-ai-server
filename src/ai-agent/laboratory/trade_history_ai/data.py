"""매매 내역 로드 및 평가용 문자열 생성. 노트북/CSV 전용."""

from pathlib import Path

import pandas as pd


def get_csv_path() -> Path:
    """이 모듈과 같은 디렉터리의 CSV 경로 (노트북·실험용, 추후 API로 교체 가능)."""
    return Path(__file__).parent / "trade_history.csv"


def load_trade_history(csv_path: Path | None = None) -> pd.DataFrame:
    """CSV에서 매매 내역을 로드하고 trade_time 오름차순 정렬하여 반환."""
    csv_path = csv_path or get_csv_path()
    df = pd.read_csv(csv_path)
    df.columns = df.columns.str.strip()
    df["trade_time"] = pd.to_datetime(df["trade_time"])
    df = df.sort_values("trade_time").reset_index(drop=True)
    return df


def get_trades_for_evaluation(
    df: pd.DataFrame,
    target_date_start: str,
    target_date_end: str,
    max_trades: int | None = 100,
) -> str:
    """평가 대상 기간의 매매 내역을 포맷된 문자열로 반환."""
    start = pd.to_datetime(target_date_start).normalize()
    end = pd.to_datetime(target_date_end).normalize() + pd.Timedelta(days=1)
    mask = (df["trade_time"] >= start) & (df["trade_time"] < end)
    block = df.loc[mask].copy()
    if max_trades is not None:
        block = block.tail(max_trades)
    lines = []
    for _, r in block.iterrows():
        side = "매도" if r["trade_type"] == 1 else "매수"
        ts = r["trade_time"].strftime("%Y-%m-%d %H:%M:%S")
        row_str = f"{ts} | {side} | {r['price']} | {r['quantity']} | {r['total_price']} | 수수료 {r['fee']}"
        if r["trade_type"] == 1 and pd.notna(r.get("profit_loss_rate")):
            row_str += f" | 손익률 {r['profit_loss_rate']}%"
            if pd.notna(r.get("avg_buy_price")):
                row_str += f" | 평균매수가 {r['avg_buy_price']}"
        lines.append(row_str)
    return "\n".join(lines) if lines else "(해당 기간 매매 없음)"
