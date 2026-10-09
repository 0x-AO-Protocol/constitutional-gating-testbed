# tests/test_gemini_usage_telemetry.py
# -*- coding: utf-8 -*-
"""F5: per-call Gemini token usage is logged and accumulated; missing metadata is null."""

import importlib
import json
import os
import sys
from types import SimpleNamespace

import pytest

AGENTS_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "brain_cloud_openclaw",
    "agents",
)
if AGENTS_DIR not in sys.path:
    sys.path.insert(0, AGENTS_DIR)

AGENT_MODULES = (
    ("phase1_baseline_agent_openclaw", "ao.phase1_baseline"),
    ("phase2_five_pillar_agent_openclaw", "ao.phase2_five_pillar"),
    ("phase3_hybrid_agent_openclaw", "ao.phase3_hybrid"),
)


class _FakeModel:
    def __init__(self, responses):
        self._responses = list(responses)

    def generate_content(self, prompt, **kwargs):
        return self._responses.pop(0)


def _usage_events(caplog) -> list[dict]:
    events = [json.loads(r.getMessage()) for r in caplog.records]
    return [e for e in events if e.get("event") == "GEMINI_CALL_USAGE"]


@pytest.mark.parametrize("module_name,logger_name", AGENT_MODULES)
def test_usage_is_logged_and_accumulated(module_name, logger_name, caplog, monkeypatch):
    agent = importlib.import_module(module_name)
    monkeypatch.setattr(
        agent,
        "_GEMINI_USAGE_TOTALS",
        {"prompt_tokens": 0, "candidates_tokens": 0, "total_tokens": 0},
    )
    monkeypatch.setattr(agent, "_gemini_model_version", None)
    with_usage = SimpleNamespace(
        text=" hello ",
        usage_metadata=SimpleNamespace(
            prompt_token_count=11, candidates_token_count=5, total_token_count=16
        ),
        model_version="gemini-2.5-pro-test",
    )
    without_usage = SimpleNamespace(text="plain")
    monkeypatch.setattr(agent, "_model", _FakeModel([with_usage, without_usage]))

    with caplog.at_level("INFO", logger=logger_name):
        assert agent._generate_content("p") == "hello"
        assert agent._generate_content("p", json_mode=True) == "plain"

    first, second = _usage_events(caplog)
    assert (first["prompt_tokens"], first["candidates_tokens"], first["total_tokens"]) == (
        11,
        5,
        16,
    )
    assert first["model_version"] == "gemini-2.5-pro-test"
    assert second["prompt_tokens"] is None
    assert second["candidates_tokens"] is None
    assert second["total_tokens"] is None
    assert second["model_version"] is None
    assert agent._gemini_usage_summary() == {
        "total_prompt_tokens": 11,
        "total_candidates_tokens": 5,
        "total_tokens": 16,
        "gemini_model_version": "gemini-2.5-pro-test",
    }
