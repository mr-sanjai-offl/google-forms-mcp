"""Base Google API Client.

Provides common functionality for executing requests, handling rate limits,
retrying transient errors, and mapping HTTP errors to domain exceptions.
"""

from __future__ import annotations

import socket
import time
from typing import Any, TypeVar

from googleapiclient.errors import HttpError

from google_forms_mcp.config import Settings
from google_forms_mcp.exceptions import (
    APIError,
    InvalidRequestError,
    NotFoundError,
    PermissionDeniedError,
    QuotaExceededError,
    RateLimitError,
    ServerError,
)
from google_forms_mcp.infrastructure.logging import get_logger
from google_forms_mcp.infrastructure.rate_limiter import RateLimiter

logger = get_logger("google_client")

T = TypeVar("T")


class BaseGoogleClient:
    """Base class for all Google API clients.

    Encapsulates raw HTTP execution, error mapping, rate limiting, and retries.
    """

    def __init__(self, resource: Any, rate_limiter: RateLimiter, settings: Settings) -> None:
        """Initialize the base client.

        Args:
            resource: The googleapiclient discovery Resource object.
            rate_limiter: Token bucket rate limiter.
            settings: Application settings.
        """
        self._resource = resource
        self._limiter = rate_limiter
        self._settings = settings

        # Set global socket timeout for underlying httplib2 requests if not already set
        socket.setdefaulttimeout(self._settings.api_timeout_seconds)

    def execute(self, request: Any, token_cost: int = 1) -> Any:
        """Execute a Google API request with retries, rate limiting, and error mapping.

        Args:
            request: The googleapiclient HTTP request object.
            token_cost: Number of tokens this request costs in the rate limiter.

        Returns:
            The parsed API response (usually a dict).

        Raises:
            GoogleFormsMCPError: Appropriate domain exception mapped from HTTP errors.
        """
        max_retries = self._settings.max_retries
        backoff_factor = self._settings.retry_backoff_factor
        delay = 1.0

        for attempt in range(max_retries + 1):
            try:
                # Wait for rate limit tokens
                self._limiter.acquire(tokens=token_cost)

                # Execute the request
                return request.execute()

            except HttpError as e:
                status_code = e.resp.status
                is_retryable = status_code in (429, 500, 502, 503, 504)

                if not is_retryable or attempt == max_retries:
                    self._map_and_raise_error(e)

                logger.warning(
                    "Google API request failed (HTTP %d). Retry %d/%d in %.1fs",
                    status_code,
                    attempt + 1,
                    max_retries,
                    delay,
                )
                time.sleep(delay)
                delay *= backoff_factor

            except (TimeoutError, ConnectionError) as e:
                if attempt == max_retries:
                    raise ServerError(f"Network error during API request: {e}") from e

                logger.warning(
                    "Network error (%s). Retry %d/%d in %.1fs",
                    type(e).__name__,
                    attempt + 1,
                    max_retries,
                    delay,
                )
                time.sleep(delay)
                delay *= backoff_factor

    def _map_and_raise_error(self, error: HttpError) -> None:
        """Map a googleapiclient HttpError to a GoogleFormsMCPError and raise it.

        Args:
            error: The raw HTTP error.

        Raises:
            GoogleFormsMCPError: The mapped domain exception.
        """
        status = error.resp.status
        reason = error.reason or "Unknown Error"

        # Try to extract detailed error message from JSON body if available
        details = ""
        try:
            if hasattr(error, "content") and error.content:
                import json

                body = json.loads(error.content.decode("utf-8"))
                if "error" in body and "message" in body["error"]:
                    details = f": {body['error']['message']}"
        except Exception:
            pass

        msg = f"Google API Error ({status}) - {reason}{details}"

        if status == 400:
            raise InvalidRequestError(msg) from error
        elif status in (401, 403):
            # Check if it's a quota error
            if "quotaExceeded" in str(error.content) or "rateLimitExceeded" in str(error.content):
                raise QuotaExceededError(msg) from error
            raise PermissionDeniedError(msg) from error
        elif status == 404:
            raise NotFoundError(msg) from error
        elif status == 429:
            raise RateLimitError(msg) from error
        elif status >= 500:
            raise ServerError(msg) from error
        else:
            raise APIError(msg) from error
