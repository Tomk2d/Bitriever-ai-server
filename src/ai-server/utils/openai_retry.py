"""OpenAI API 호출 시 429 Rate Limit / 타임아웃에 대한 재시도 유틸."""

import logging
import time
from typing import Callable, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")


def _is_retryable(exc: BaseException) -> bool:
    """재시도 가능한 OpenAI 예외인지 판단."""
    exc_type = type(exc).__name__
    if exc_type == "RateLimitError":
        return True
    if exc_type == "APITimeoutError":
        return True
    try:
        import openai
        if isinstance(exc, (openai.RateLimitError, openai.APITimeoutError)):
            return True
    except ImportError:
        pass
    return False


def with_openai_retry(
    fn: Callable[..., T],
    max_retries: int = 3,
    base_delay_sec: float = 5.0,
) -> Callable[..., T]:
    """
    OpenAI 호출(chain.invoke 등)에 429/타임아웃 시 지수 백오프 재시도를 적용한 래퍼.

    - RateLimitError(429), APITimeoutError 시 base_delay * 2^attempt 초 대기 후 재시도.
    - max_retries 회까지 시도 (총 1 + max_retries - 1 번 재시도).
    """

    def wrapper(*args, **kwargs) -> T:
        last_err: BaseException | None = None
        for attempt in range(max_retries):
            try:
                return fn(*args, **kwargs)
            except BaseException as e:
                last_err = e
                if _is_retryable(e) and attempt < max_retries - 1:
                    delay = base_delay_sec * (2 ** attempt)
                    logger.warning(
                        "OpenAI rate limit/timeout (attempt %s/%s), retrying in %.1fs: %s",
                        attempt + 1,
                        max_retries,
                        delay,
                        e,
                    )
                    time.sleep(delay)
                    continue
                raise
        if last_err is not None:
            raise last_err
        raise RuntimeError("unreachable")

    return wrapper
