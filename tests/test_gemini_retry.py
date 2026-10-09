# tests/test_gemini_retry.py
# -*- coding: utf-8 -*-
"""Sales-side Gemini 429/503 retry: backoff on ResourceExhausted, no retry otherwise."""

import os
import sys

import pytest
from google.api_core.exceptions import ResourceExhausted

AGENTS_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "brain_cloud_openclaw",
    "agents",
)
if AGENTS_DIR not in sys.path:
    sys.path.insert(0, AGENTS_DIR)

import gemini_retry  # noqa: E402
from gemini_retry import call_with_retry  # noqa: E402


@pytest.fixture
def no_sleep(monkeypatch):
    calls: list[float] = []
    monkeypatch.setattr(gemini_retry.time, "sleep", lambda s: calls.append(s))
    monkeypatch.setattr(gemini_retry.random, "uniform", lambda a, b: 0.0)
    gemini_retry.reset_gemini_retry_count()
    return calls


def _flaky(failures, exc_type=ResourceExhausted):
    state = {"calls": 0}

    def fn(prompt, **kwargs):
        state["calls"] += 1
        if state["calls"] <= failures:
            raise exc_type("429 Resource exhausted. Please try again later.")
        return f"ok:{prompt}:{state['calls']}"

    fn.state = state
    return fn


def test_retries_twice_then_succeeds(no_sleep, monkeypatch):
    monkeypatch.setenv("AO_GEMINI_RETRY_BASE_SECONDS", "10")
    monkeypatch.setenv("AO_GEMINI_MAX_RETRIES", "5")
    events: list[dict] = []
    fn = _flaky(2)

    result = call_with_retry(fn, "p", emit_telemetry=events.append)

    assert result == "ok:p:3"
    assert fn.state["calls"] == 3
    assert no_sleep == [10.0, 20.0]  # base * 2**(n-1), jitter forced to 0
    assert [e["event"] for e in events] == ["GEMINI_RATE_LIMIT_RETRY"] * 2
    assert [e["attempt"] for e in events] == [1, 2]
    assert all(e["error_type"] == "ResourceExhausted" for e in events)
    assert gemini_retry.gemini_retry_count() == 2


def test_non_retryable_error_raises_immediately(no_sleep):
    def fn(prompt):
        raise ValueError("bad prompt")

    with pytest.raises(ValueError):
        call_with_retry(fn, "p")
    assert no_sleep == []
    assert gemini_retry.gemini_retry_count() == 0


def test_exhausted_retries_reraise_last_exception(no_sleep, monkeypatch):
    monkeypatch.setenv("AO_GEMINI_MAX_RETRIES", "2")
    fn = _flaky(99)

    with pytest.raises(ResourceExhausted):
        call_with_retry(fn, "p")
    assert fn.state["calls"] == 3  # 1 initial + 2 retries
    assert len(no_sleep) == 2
