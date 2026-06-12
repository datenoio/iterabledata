"""
Utility functions for AI operations including retry logic.
"""

from __future__ import annotations

import time
from collections.abc import Callable
from typing import TypeVar

import requests

T = TypeVar("T")


def retry_with_backoff(
    func: Callable[[], T],
    max_retries: int = 3,
    initial_delay: float = 1.0,
    backoff_factor: float = 2.0,
    retry_statuses: tuple[int, ...] = (429, 500, 502, 503, 504),
) -> T:
    """
    Retry a function with exponential backoff for rate limiting and server errors.

    Args:
        func: Function to retry (should raise requests.exceptions.RequestException)
        max_retries: Maximum number of retry attempts
        initial_delay: Initial delay in seconds before first retry
        backoff_factor: Factor to multiply delay by for each retry
        retry_statuses: HTTP status codes that should trigger a retry

    Returns:
        Result of the function call

    Raises:
        requests.exceptions.RequestException: If all retries are exhausted
    """
    delay = initial_delay
    last_exception = None

    for attempt in range(max_retries + 1):
        try:
            return func()
        except requests.exceptions.RequestException as e:
            last_exception = e
            status_code = getattr(e.response, "status_code", None) if hasattr(e, "response") else None

            # Only retry on specific status codes or if status_code is None (network error)
            if status_code not in retry_statuses and status_code is not None:
                raise

            # Don't retry on last attempt
            if attempt >= max_retries:
                break

            # Extract retry-after header if present (for 429 errors)
            retry_after = None
            if hasattr(e, "response") and e.response is not None:
                retry_after = e.response.headers.get("Retry-After")
                if retry_after:
                    try:
                        delay = float(retry_after)
                    except ValueError:
                        pass

            # Wait before retrying
            time.sleep(delay)
            delay *= backoff_factor

    # All retries exhausted, raise last exception
    if last_exception:
        raise last_exception
    raise RuntimeError("Retry logic failed unexpectedly")
