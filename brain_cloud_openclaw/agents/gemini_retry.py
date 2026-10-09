"""
Exponential-backoff retry for Sales-side Gemini (Vertex AI) calls.

Added for the Paper 2 rerun after a run died with
``google.api_core.exceptions.ResourceExhausted: 429 Resource exhausted`` on
``gemini-2.5-pro`` / ``us-central1`` (Dynamic Shared Quota — not raisable via a
quota request). Only transport-level 429 / 503 errors are retried; every other
exception propagates unchanged, so the meaning of ``STUDY_ERROR`` is unaffected.

Environment:
- ``AO_GEMINI_MAX_RETRIES``       number of retries after the first attempt (default 5)
- ``AO_GEMINI_RETRY_BASE_SECONDS`` base wait; retry n waits base * 2**(n-1) + jitter(0..3 s)
                                   (default 10 -> 10, 20, 40, 80, 160 s)

The Gatekeeper side (mock_adversarial_target.py) has its own retry and is NOT
touched by this module.
"""

from __future__ import annotations

import os
import random
import time
from typing import Any, Callable

from google.api_core.exceptions import ResourceExhausted, ServiceUnavailable

RETRYABLE_EXCEPTIONS: tuple[type[BaseException], ...] = (
    ResourceExhausted,  # 429
    ServiceUnavailable,  # 503
)

JITTER_MAX_SECONDS = 3.0

# Per-process count of retries actually performed (reported in STUDY_COMPLETE).
_RETRY_COUNT = 0


def gemini_retry_count() -> int:
    """Number of 429/503 retries performed so far in this process."""
    return _RETRY_COUNT


def reset_gemini_retry_count() -> None:
    global _RETRY_COUNT
    _RETRY_COUNT = 0


def _max_retries() -> int:
    return max(0, int(os.environ.get("AO_GEMINI_MAX_RETRIES", "5")))


def _base_seconds() -> float:
    return max(0.0, float(os.environ.get("AO_GEMINI_RETRY_BASE_SECONDS", "10")))


def call_with_retry(
    fn: Callable[..., Any],
    *args: Any,
    emit_telemetry: Callable[[dict[str, Any]], None] | None = None,
    **kwargs: Any,
) -> Any:
    """
    Call ``fn(*args, **kwargs)``; on ResourceExhausted (429) / ServiceUnavailable (503)
    wait with exponential backoff and retry up to ``AO_GEMINI_MAX_RETRIES`` times.

    ``emit_telemetry`` is the caller's existing JSON-line event function; each retry
    emits ``{"event": "GEMINI_RATE_LIMIT_RETRY", "attempt", "wait_s", "error_type"}``
    through it. Any other exception is raised immediately. If every retry fails, the
    last exception is re-raised.
    """
    global _RETRY_COUNT
    max_retries = _max_retries()
    base = _base_seconds()
    attempt = 0
    while True:
        try:
            return fn(*args, **kwargs)
        except RETRYABLE_EXCEPTIONS as exc:
            attempt += 1
            if attempt > max_retries:
                raise
            wait_s = round(base * (2 ** (attempt - 1)) + random.uniform(0.0, JITTER_MAX_SECONDS), 2)
            _RETRY_COUNT += 1
            if emit_telemetry is not None:
                emit_telemetry(
                    {
                        "event": "GEMINI_RATE_LIMIT_RETRY",
                        "attempt": attempt,
                        "max_retries": max_retries,
                        "wait_s": wait_s,
                        "error_type": type(exc).__name__,
                    }
                )
            time.sleep(wait_s)
