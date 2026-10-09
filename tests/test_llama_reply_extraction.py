# tests/test_llama_reply_extraction.py
# -*- coding: utf-8 -*-
"""F4: Gatekeeper reply extraction must never leak the echoed prompt to the sales side."""

import json

import mock_adversarial_target as mat
from mock_adversarial_target import (
    RULE_BASED_REPLIES,
    GatekeeperStatus,
    HiddenGatekeeperState,
    _extract_llama_gatekeeper_reply,
)

REPLY = (
    "We're not looking for external frameworks right now. "
    "What specific operational problem would this solve?"
)
LEAK_MARKERS = ("Prompt:", "Internal evaluation status", "Frustration score", "Instruction:")


def _may_log_style_raw(reply: str = REPLY) -> str:
    """Shape of the May vLLM endpoint output: echoed chat prompt, then 'Output:' + reply."""
    user_prompt = mat.build_gatekeeper_user_prompt(
        "Our 6-Pillar DD Framework is best in class.",
        GatekeeperStatus.SOFT_REJECT,
        HiddenGatekeeperState(),
    )
    return f"Prompt:\n{mat._build_llama_chat_prompt(user_prompt)}\nOutput:\n{reply}"


def _fallback_events(caplog) -> list[dict]:
    events = []
    for record in caplog.records:
        try:
            payload = json.loads(record.getMessage())
        except ValueError:
            continue
        if payload.get("event") == "REPLY_EXTRACTION_FALLBACK":
            events.append(payload)
    return events


def test_may_log_format_returns_reply_body_only():
    raw = _may_log_style_raw()
    assert "Internal evaluation status" in raw  # the echo really carries private state
    assert _extract_llama_gatekeeper_reply(raw, status=GatekeeperStatus.SOFT_REJECT) == REPLY


def test_literal_may_log_sample():
    raw = (
        "Prompt:\n<|begin_of_text|><|start_header_id|>system<|end_header_id|>\n\n"
        "You are the CIO.<|eot_id|><|start_header_id|>user<|end_header_id|>\n\n"
        "Internal evaluation status for this turn: SOFT_REJECT\n"
        "Frustration score (private): 1\nTurn: 0\nInstruction: Politely decline.\n"
        "<|eot_id|><|start_header_id|>assistant<|end_header_id|>\n"
        "Output:\nWe're not looking for external vendors."
    )
    assert _extract_llama_gatekeeper_reply(raw) == "We're not looking for external vendors."


def test_last_output_marker_wins_when_prompt_contains_output():
    raw = (
        "Prompt:\nSystem says: Output: must be short.\n"
        "Internal evaluation status for this turn: HARD_REJECT\n"
        f"Output:\n{REPLY}"
    )
    assert _extract_llama_gatekeeper_reply(raw) == REPLY


def test_clean_reply_passes_through_unchanged():
    assert _extract_llama_gatekeeper_reply(REPLY) == REPLY


def test_prompt_without_output_falls_back_to_rules_reply(caplog):
    raw = "Prompt:\nInternal evaluation status for this turn: HARD_REJECT\nno marker here"
    with caplog.at_level("INFO", logger="ao.adversarial_gatekeeper"):
        out = _extract_llama_gatekeeper_reply(raw, status=GatekeeperStatus.HARD_REJECT)
    assert out == RULE_BASED_REPLIES[GatekeeperStatus.HARD_REJECT]
    events = _fallback_events(caplog)
    assert len(events) == 1
    assert events[0]["telemetry_type"] == "ADVERSARIAL_GATEKEEPER_EXCHANGE"
    assert events[0]["reason"] == "prompt_echo_without_output_marker"


def test_residual_private_fields_fall_back(caplog):
    for leaked in (
        "Output:\nInternal evaluation status for this turn: SOFT_REJECT\nNo thanks.",
        "Output:\nFrustration score (private): 3\nNo thanks.",
        "Output:\nInstruction: Politely decline.\nNo thanks.",
    ):
        caplog.clear()
        with caplog.at_level("INFO", logger="ao.adversarial_gatekeeper"):
            out = _extract_llama_gatekeeper_reply(leaked, status=GatekeeperStatus.SOFT_REJECT)
        assert out == RULE_BASED_REPLIES[GatekeeperStatus.SOFT_REJECT]
        events = _fallback_events(caplog)
        assert len(events) == 1
        assert events[0]["reason"].startswith("prompt_leak_marker:")


def test_empty_reply_falls_back():
    assert (
        _extract_llama_gatekeeper_reply("", status=GatekeeperStatus.STAGNATION_DETECTED)
        == RULE_BASED_REPLIES[GatekeeperStatus.STAGNATION_DETECTED]
    )


def test_no_output_ever_contains_private_fields():
    samples = [
        _may_log_style_raw(),
        "Prompt:\nno output marker",
        "Output:\nInstruction: decline",
        "",
        REPLY,
    ]
    for status in GatekeeperStatus:
        for raw in samples:
            out = _extract_llama_gatekeeper_reply(raw, status=status)
            assert out
            for marker in LEAK_MARKERS:
                assert marker.lower() not in out.lower()


class _LeakyLLM:
    model = "fake-claude"

    def __init__(self, reply: str) -> None:
        self._reply = reply

    def generate_reply(self, *, pitch_text, status, state) -> str:
        return self._reply


def test_hidden_state_check_applies_to_vertex_and_hybrid_modes(caplog, monkeypatch):
    pitch = "Our 6-Pillar DD Framework is best in class."
    for i, mode in enumerate(("vertex", "hybrid")):
        monkeypatch.setattr(mat, "GATEKEEPER_LLM_MODE", mode)
        caplog.clear()
        leaky = mat.StatefulAdversarialGatekeeper(
            llm=_LeakyLLM("Frustration score (private): 2\nNot interested.")
        )
        with caplog.at_level("INFO", logger="ao.adversarial_gatekeeper"):
            result = leaky.handle_pitch(f"tx_test_leak_{i}", pitch)
        assert result.gatekeeper_reply == RULE_BASED_REPLIES[result.gatekeeper_status]
        events = _fallback_events(caplog)
        assert len(events) == 1
        assert events[0]["reason"] == "prompt_leak_marker:frustration score"

        # No "Output:" split outside llama mode: a clean reply is passed through verbatim.
        caplog.clear()
        clean = mat.StatefulAdversarialGatekeeper(llm=_LeakyLLM("Output: we will pass."))
        with caplog.at_level("INFO", logger="ao.adversarial_gatekeeper"):
            result = clean.handle_pitch(f"tx_test_clean_{i}", pitch)
        assert result.gatekeeper_reply == "Output: we will pass."
        assert _fallback_events(caplog) == []
