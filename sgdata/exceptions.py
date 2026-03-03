"""SGData SDK exception hierarchy."""

from typing import Optional
import requests


class SGDataError(Exception):
    """Base exception for all SGData SDK errors."""


class SGDataAPIError(SGDataError):
    """Raised for HTTP 4xx (except 429) and 5xx responses."""

    def __init__(self, message: str, status_code: int, response: requests.Response) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.response = response


class RateLimitError(SGDataError):
    """Raised when the API returns HTTP 429 Too Many Requests."""

    def __init__(self, message: str, response: requests.Response) -> None:
        super().__init__(message)
        self.response = response


class SGDataTimeoutError(SGDataError):
    """Raised when a request times out."""
