"""Exponential backoff retry logic for Google API calls.

Handles transient errors (429, 500, 503) with configurable retry parameters.
"""

from __future__ import annotations

import random
import time
from collections.abc import Callable
from functools import wraps
from typing import Any, TypeVar

from googleapiclient.errors import HttpError

from google_forms_mcp.exceptions import (
    InvalidRequestError,
    NotFoundError,
    PermissionDeniedError,
    RateLimitError,
    ServerError,
)
from google_forms_mcp.infrastructure.logging import get_logger

logger = get_logger("retry")

F = TypeVar("F", bound=Callable[..., Any])

# HTTP status codes that are retryable
RETRYABLE_STATUS_CODES = {429, 500, 502, 503}

# Default retry configuration
DEFAULT_MAX_RETRIES = 5
DEFAULT_BASE_DELAY = 1.0  # seconds
DEFAULT_MAX_DELAY = 60.0  # seconds
DEFAULT_JITTER = True


def with_retry(
    max_retries: int = DEFAULT_MAX_RETRIES,
    base_delay: float = DEFAULT_BASE_DELAY,
    max_delay: float = DEFAULT_MAX_DELAY,
    jitter: bool = DEFAULT_JITTER,
) -> Callable[[F], F]:
    """Decorator that retries a function on transient Google API errors.

    Uses exponential backoff with optional jitter. Only retries on status codes
    known to be transient (429, 500, 502, 503).

    Args:
        max_retries: Maximum number of retry attempts.
        base_delay: Initial delay in seconds.
        max_delay: Maximum delay between retries.
        jitter: Whether to add random jitter to delay.

    Returns:
        Decorated function with retry behavior.
    """

    def decorator(func: F) -> F:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            last_exception: Exception | None = None

            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except HttpError as e:
                    status = e.resp.status if e.resp else 0
                    last_exception = e

                    if status not in RETRYABLE_STATUS_CODES:
                        # Non-retryable error — translate and raise immediately
                        _translate_http_error(e)

                    if attempt == max_retries:
                        # Exhausted all retries
                        logger.error(
                            "Max retries (%d) exhausted for %s: HTTP %d",
                            max_retries,
                            func.__name__,
                            status,
                        )
                        if status == 429:
                            raise RateLimitError() from e
                        raise ServerError(
                            f"Google API server error (HTTP {status}) after {max_retries} retries.",
                            status_code=status,
                        ) from e

                    # Calculate delay with exponential backoff
                    delay = min(base_delay * (2**attempt), max_delay)
                    if jitter:
                        delay = delay * (0.5 + random.random())

                    logger.warning(
                        "Retryable error (HTTP %d) in %s, attempt %d/%d. "
                        "Retrying in %.1fs...",
                        status,
                        func.__name__,
                        attempt + 1,
                        max_retries,
                        delay,
                    )
                    time.sleep(delay)

            # Should not reach here, but just in case
            if last_exception:
                raise last_exception
            raise RuntimeError("Unexpected retry loop exit")

        return wrapper  # type: ignore[return-value]

    return decorator


def _translate_http_error(error: HttpError) -> None:
    """Translate a Google API HttpError into a domain-specific exception.

    Args:
        error: The HttpError from google-api-python-client.

    Raises:
        Domain-specific exception based on the HTTP status code.
    """
    status = error.resp.status if error.resp else 0
    reason = str(error)

    if status == 400:
        raise InvalidRequestError(
            f"Bad request: {reason}",
            status_code=400,
        ) from error
    elif status == 401:
        from google_forms_mcp.exceptions import TokenExpiredError

        raise TokenExpiredError(
            "Authentication token expired or invalid. Please re-authenticate."
        ) from error
    elif status == 403:
        raise PermissionDeniedError() from error
    elif status == 404:
        raise NotFoundError("Resource", "unknown") from error
    elif status == 429:
        raise RateLimitError() from error
    elif status >= 500:
        raise ServerError(
            f"Google API server error (HTTP {status}): {reason}",
            status_code=status,
        ) from error
    else:
        from google_forms_mcp.exceptions import APIError

        raise APIError(
            f"Google API error (HTTP {status}): {reason}",
            status_code=status,
        ) from error
