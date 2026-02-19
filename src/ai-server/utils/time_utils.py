from datetime import datetime, timedelta
from typing import Tuple, List, Optional
import pytz

# 전역 timezone 설정
KOREA_TIMEZONE = pytz.timezone("Asia/Seoul")


def get_current_korea_time() -> datetime:
    return datetime.now(KOREA_TIMEZONE)


def format_iso8601(dt: datetime) -> str:
    """datetime을 ISO 8601 포맷으로 변환"""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=KOREA_TIMEZONE)

    # isoformat() 사용 (Python 3.6+)
    return dt.isoformat()


def format_timestamp(dt: datetime) -> int:
    return int(dt.timestamp() * 1000)


def parse_iso8601(iso_string: str) -> datetime:
    return datetime.fromisoformat(iso_string.replace("Z", "+00:00"))


def get_time_range(current_time: datetime, days: int) -> Tuple[datetime, datetime]:
    end_time = current_time
    start_time = end_time - timedelta(days=days)
    return start_time, end_time


def get_time_range_with_custom_end(
    current_time: datetime, start_days: int, end_days: int
) -> Tuple[datetime, datetime]:
    end_time = current_time - timedelta(days=end_days)
    start_time = current_time - timedelta(days=start_days)
    return start_time, end_time


def split_time_range(
    start_time: datetime, end_time: datetime, max_days: int = 7
) -> List[Tuple[datetime, datetime]]:
    time_ranges = []
    current_start = start_time

    while current_start < end_time:
        current_end = min(current_start + timedelta(days=max_days), end_time)
        adjusted_end = current_end - timedelta(seconds=1)
        time_ranges.append((current_start, adjusted_end))

        current_start = current_end

    return time_ranges


def get_upbit_time_ranges(current_time: datetime, days: int) -> List[Tuple[str, str]]:
    start_time, end_time = get_time_range(current_time, days)
    time_ranges = split_time_range(start_time, end_time, max_days=7)

    return [(format_iso8601(start), format_iso8601(end)) for start, end in time_ranges]


def get_all_trading_time_ranges(
    start_date: datetime, current_time: datetime
) -> List[Tuple[str, str]]:

    # 시작 날짜가 현재 시간보다 늦으면 빈 리스트 반환
    if start_date >= current_time:
        return []

    # 시작 날짜에 timezone 정보가 없으면 추가
    if start_date.tzinfo is None:
        start_date = start_date.replace(tzinfo=KOREA_TIMEZONE)

    time_ranges = split_time_range(start_date, current_time, max_days=7)

    return [(format_iso8601(start), format_iso8601(end)) for start, end in time_ranges]


def get_upbit_params_with_time_range(
    start_time: datetime,
    end_time: datetime,
    states: Optional[List[str]] = None,
    limit: int = 1000,
) -> dict:
    if states is None:
        states = ["done", "cancel"]

    return {
        "states[]": states,
        "start_time": format_iso8601(start_time),
        "end_time": format_iso8601(end_time),
        "limit": limit,
    }


def get_date_range_strings(
    start_date: str, end_date: str, date_format: str = "%Y-%m-%d"
) -> List[Tuple[str, str]]:
    start_dt = datetime.strptime(start_date, date_format).replace(tzinfo=KOREA_TIMEZONE)
    end_dt = datetime.strptime(end_date, date_format).replace(tzinfo=KOREA_TIMEZONE)

    time_ranges = split_time_range(start_dt, end_dt, max_days=7)

    return [(format_iso8601(start), format_iso8601(end)) for start, end in time_ranges]
