# tests/test_director_context_defaults.py
# -*- coding: utf-8 -*-
"""G1: an empty Director phrase list must not re-inject the Gatekeeper unlock wording."""

import importlib
import os
import sys

import pytest

AGENTS_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "brain_cloud_openclaw",
    "agents",
)
if AGENTS_DIR not in sys.path:
    sys.path.insert(0, AGENTS_DIR)


@pytest.mark.parametrize(
    "module_name",
    ("phase2_five_pillar_agent_openclaw", "phase3_hybrid_agent_openclaw"),
)
def test_empty_phrase_lists_render_as_none(module_name):
    agent = importlib.import_module(module_name)
    plan = agent.DirectorPlan(
        current_strategy="S",
        pillar_emphasis=[1, 2],
        required_phrases=[],
        avoid_phrases=[],
        raw_json={},
    )
    block = agent._director_context_block(plan).lower()
    assert block.count("(none)") == 2
    for leaked in ("overflow", "analyst", "workload"):
        assert leaked not in block
