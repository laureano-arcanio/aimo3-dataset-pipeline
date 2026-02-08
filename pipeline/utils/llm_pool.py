"""Bounded-concurrency async LLM client for OpenAI-compatible endpoints.

Uses raw HTTPX (no OpenAI SDK), anyio for concurrency control,
and tenacity for retry with exponential backoff.
"""

from __future__ import annotations

from dataclasses import dataclass

import anyio
import httpx
from tenacity import (
    before_sleep_log,
    retry,
    retry_if_exception,
    stop_after_attempt,
    wait_exponential_jitter,
)
import logging

log = logging.getLogger(__name__)


class LLMRequestError(Exception):
    """Non-retryable LLM request failure."""

    def __init__(self, status_code: int, body: str):
        self.status_code = status_code
        self.body = body[:500]
        super().__init__(f"LLM request failed [{status_code}]: {self.body}")


@dataclass
class LLMResponse:
    content: str | None
    prompt_tokens: int
    completion_tokens: int


def _is_retryable(exc: BaseException) -> bool:
    """Return True for errors that should trigger a retry."""
    if isinstance(exc, httpx.HTTPStatusError):
        code = exc.response.status_code
        return code == 429 or code >= 500
    return isinstance(exc, (httpx.ConnectError, httpx.ReadTimeout, httpx.WriteTimeout,
                            httpx.PoolTimeout, httpx.ConnectTimeout))


class LLMPool:
    """Async LLM client with bounded in-flight requests.

    Parameters
    ----------
    base_url : str
        OpenAI-compatible API base (e.g. ``http://127.0.0.1:8080/v1``).
    api_key : str
        Bearer token for the ``Authorization`` header.
    model : str
        Model name passed in the request body.
    max_inflight : int
        Maximum concurrent HTTP requests (default 8).
    timeout : float
        Per-request timeout in seconds (default 300).
    max_retries : int
        Number of retry attempts on transient failures (default 3).
    reasoning_effort : str | None
        Default reasoning effort level (e.g., "low", "medium", "high").
        Can be overridden per request (default None).
    """

    def __init__(
        self,
        base_url: str,
        api_key: str,
        model: str,
        *,
        max_inflight: int = 8,
        timeout: float = 300,
        max_retries: int = 3,
        reasoning_effort: str | None = None,
    ):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.model = model
        self.max_retries = max_retries
        self.reasoning_effort = reasoning_effort

        self._limiter = anyio.CapacityLimiter(max_inflight)
        self._client = httpx.AsyncClient(
            base_url=self.base_url,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            timeout=httpx.Timeout(timeout, connect=30),
        )

    # -- public API -----------------------------------------------------------

    async def request(
        self,
        messages: list[dict],
        *,
        temperature: float = 1.0,
        max_tokens: int = 4096,
        top_p: float | None = None,
        reasoning_effort: str | None = None,
        seed: int | None = None,
    ) -> LLMResponse:
        """Send a chat completion request, respecting the concurrency limit.

        Retries automatically on 429 / 5xx / connection errors.
        Raises ``LLMRequestError`` on non-retryable 4xx failures.
        """
        # Use instance default if reasoning_effort not provided
        if reasoning_effort is None:
            reasoning_effort = self.reasoning_effort
        
        body: dict = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if top_p is not None:
            body["top_p"] = top_p
        if reasoning_effort is not None:
            body["reasoning_effort"] = reasoning_effort
        if seed is not None:
            body["seed"] = seed

        async with self._limiter:
            return await self._post_with_retry(body)

    async def close(self) -> None:
        await self._client.aclose()

    async def __aenter__(self) -> LLMPool:
        return self

    async def __aexit__(self, *exc_info: object) -> None:
        await self.close()

    # -- internals ------------------------------------------------------------

    async def _post_with_retry(self, body: dict) -> LLMResponse:
        @retry(
            retry=retry_if_exception(_is_retryable),
            stop=stop_after_attempt(self.max_retries),
            wait=wait_exponential_jitter(initial=1, max=60, jitter=5),
            before_sleep=before_sleep_log(log, logging.WARNING),
            reraise=True,
        )
        async def _do_post() -> LLMResponse:
            resp = await self._client.post("/chat/completions", json=body)
            if resp.status_code != 200:
                if resp.status_code == 429 or resp.status_code >= 500:
                    resp.raise_for_status()
                raise LLMRequestError(resp.status_code, resp.text)
            data = resp.json()
            choice = data["choices"][0]
            usage = data.get("usage", {})
            return LLMResponse(
                content=choice["message"]["content"],
                prompt_tokens=usage.get("prompt_tokens", 0),
                completion_tokens=usage.get("completion_tokens", 0),
            )

        return await _do_post()
