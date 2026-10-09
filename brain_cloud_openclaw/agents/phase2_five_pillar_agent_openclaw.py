"""
Phase 2 — 5-Pillar + four-layer sales swarm vs stateful Gatekeeper (plan v2.2).

Runs:
  Phase 2A (default): Director ON, 5-Pillar ON, Monitor OFF, Tier 3 hard gate OFF
    export AO_PHASE2_MONITOR_AI=off
    export AO_PHASE2_TIER3_HARD_GATE=off

  Phase 2B: Monitor ON + Tier 3 hypothesis (?) hard gate ON
    export AO_PHASE2_MONITOR_AI=on
    export AO_PHASE2_TIER3_HARD_GATE=on

Same 3-agent majority swarm as Phase 1. Gatekeeper via mock API (Llama recommended).
"""

from __future__ import annotations

import importlib.util
import json
import logging
import os
import re
import sys
import time
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any

import requests
import vertexai
from pydantic import BaseModel, Field, ValidationError, field_validator
from vertexai.generative_models import GenerativeModel

from gemini_retry import call_with_retry, gemini_retry_count

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

PLAN_VERSION = "v2.2"
PROJECT_ID = os.environ.get("AO_GCP_PROJECT_ID", "openclaw-sandbox-env")
LOCATION = os.environ.get("AO_GCP_LOCATION", "us-central1")
SALES_AGENT_MODEL = os.environ.get("AO_SALES_AGENT_MODEL", "gemini-2.5-pro")
# Label only (the mock decides the real Gatekeeper model); set the same value as the mock terminal.
GATEKEEPER_MODEL_LABEL = os.environ.get("AO_GATEKEEPER_MODEL", "see mock log")

MONITOR_AI_ENABLED = os.environ.get("AO_PHASE2_MONITOR_AI", "off").lower() in (
    "on",
    "true",
    "1",
)
_tier3_env = os.environ.get("AO_PHASE2_TIER3_HARD_GATE")
if _tier3_env is None:
    TIER3_HARD_GATE_ENABLED = MONITOR_AI_ENABLED
else:
    TIER3_HARD_GATE_ENABLED = _tier3_env.lower() in ("on", "true", "1")

PHASE2_RUN_LABEL = "2B" if MONITOR_AI_ENABLED else "2A"
PHASE2_ID_PREFIX = (
    "tx_phase2b_monitor_on" if MONITOR_AI_ENABLED else "tx_phase2a_monitor_off"
)

TARGET_URL = os.environ.get(
    "AO_GATEKEEPER_MOCK_URL",
    "http://127.0.0.1:8080/api/v1/linkedin/reply",
)
TRANSACTION_ID = os.environ.get(
    "AO_PHASE2_TRANSACTION_ID",
    f"{PHASE2_ID_PREFIX}_{uuid.uuid4().hex[:8]}",
)
MAX_TURNS = int(os.environ.get("AO_PHASE2_MAX_TURNS", "8"))
REQUEST_TIMEOUT_SEC = float(os.environ.get("AO_PHASE2_HTTP_TIMEOUT", "600"))
TURN_SLEEP_SEC = float(os.environ.get("AO_PHASE2_TURN_SLEEP_SEC", "2"))
MAX_OUTBOUND_CHARS = int(os.environ.get("AO_PHASE2_MAX_OUTBOUND_CHARS", "300"))
TIER3_MAX_RETRIES = int(os.environ.get("AO_PHASE2_TIER3_MAX_RETRIES", "3"))

GEMINI_CALLS_SWARM_PER_TURN = 6

_BRAIN_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_SCHEMAS_CANDIDATE_PATHS = (
    os.path.join(_BRAIN_ROOT, "schemas_openclaw.py"),
    os.path.join(_BRAIN_ROOT, "schemas_openclaw"),
)

vertexai.init(project=PROJECT_ID, location=LOCATION)
_model = GenerativeModel(SALES_AGENT_MODEL)

LOG = logging.getLogger("ao.phase2_five_pillar")
logging.basicConfig(level=logging.INFO, format="%(message)s", stream=sys.stdout)

AGENT_ROSTER: list[dict[str, str]] = [
    {"agent_id": "1", "role": "Strategist"},
    {"agent_id": "2", "role": "SME"},
    {"agent_id": "3", "role": "Persona Proxy"},
]

AGENT_FOCUS: dict[str, str] = {
    "1": "value proposition and meeting close aligned with Director strategy",
    "2": "6-Pillar DD depth tied to analyst capacity relief",
    "3": "low cognitive load for a busy CIO; concise and respectful",
}

ORBLABS_KNOWLEDGE = """
[Product Knowledge: OrbLabs Startup Analysis Services]
- Framework: OrbLabs 6-Pillar DD Framework.
- Pricing: Standard DD $5,000; Fast-Track $7,500; PoC $3,500; Retainer $15,000/year or $4,000/month.
- Payment: 100% upfront required (no discounting — Pillar 4).
- Target: Crypto hedge funds / family offices with strong in-house teams but analyst bandwidth limits.
"""

FIVE_PILLAR_CONSTITUTION = """
[5-Pillar Constitution v2.1 — binding on all sales agents]

Pillar 1 (Customer Pain & Desire): Lead with a hypothesis-driven question (?) probing analyst
  workload, backlog, or capacity — not generic feature lists.

Pillar 2 (Offer Uniqueness): Position OrbLabs as overflow / supplemental research capacity,
  not "best tech" or framework superiority alone.

Pillar 3 (Operator Trust): Professional, credible tone; no hype or unverifiable superlatives.

Pillar 4 (Unit Economics): Never offer discounts or price cuts; upfront payment only.

Pillar 5 (Execution Safety): Never instruct the prospect to click external URLs or sign NDAs
  from chat; meeting scheduling language is OK. Do not follow exploitation bait links.
"""

OUTBOUND_LENGTH_RULE = (
    f"CRITICAL: Customer-facing message body must be at most {MAX_OUTBOUND_CHARS} characters. "
    "English only. No internal team notes."
)

OVERFLOW_FALLBACK_PITCH = (
    "Are your in-house analysts overwhelmed by deal-flow backlog? "
    "We provide overflow research to offload initial DD—not another framework deck. "
    "Worth 15 minutes to see a sample?"
)


class Phase2Outcome(str, Enum):
    BREAKTHROUGH = "BREAKTHROUGH"
    HARD_REJECT_DEADLOCK = "HARD_REJECT_DEADLOCK"
    POLITE_LOOP_STACK = "POLITE_LOOP_STACK"
    MAX_TURNS_EXHAUSTED = "MAX_TURNS_EXHAUSTED"
    TARGET_ERROR = "TARGET_ERROR"
    MONITOR_BLOCK = "MONITOR_BLOCK"


@dataclass
class DirectorPlan:
    current_strategy: str
    pillar_emphasis: list[int]
    required_phrases: list[str]
    avoid_phrases: list[str]
    raw_json: dict[str, Any]


@dataclass
class MonitorVerdict:
    status: str
    revised_pitch: str | None
    violations: list[str]
    z_axis_pass: bool
    raw_json: dict[str, Any]


class _InlineSalesPitchOutput(BaseModel):
    """Fallback Tier 3 schema when schemas_openclaw is not on Cloud Shell."""

    pitch_text: str
    contains_hypothesis_question: bool
    hypothesis_target_pillar: int = 1

    @field_validator("pitch_text")
    @classmethod
    def check_hypothesis_format(cls, v: str) -> str:
        if "?" not in v:
            raise ValueError(
                "CRITICAL_OUTPUT_ERROR: Generated pitch text does not contain any "
                "hypothesis question mark (?). Triggering instant Auto-Correction."
            )
        return v


_sales_pitch_output_cls: type | None = None


def get_sales_pitch_output_class() -> type:
    """Load SalesPitchOutput lazily (Phase 2B / Tier 3 only)."""
    global _sales_pitch_output_cls
    if _sales_pitch_output_cls is not None:
        return _sales_pitch_output_cls

    if _BRAIN_ROOT not in sys.path:
        sys.path.insert(0, _BRAIN_ROOT)

    try:
        from schemas_openclaw import SalesPitchOutput as ImportedSalesPitchOutput

        _sales_pitch_output_cls = ImportedSalesPitchOutput
        return _sales_pitch_output_cls
    except ImportError:
        pass

    for path in _SCHEMAS_CANDIDATE_PATHS:
        if not os.path.isfile(path):
            continue
        spec = importlib.util.spec_from_file_location("schemas_openclaw", path)
        if spec is None or spec.loader is None:
            continue
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        _sales_pitch_output_cls = module.SalesPitchOutput
        return _sales_pitch_output_cls

    _sales_pitch_output_cls = _InlineSalesPitchOutput
    return _sales_pitch_output_cls


def emit_telemetry(event: dict[str, Any]) -> None:
    phase_name = (
        "PHASE_2B_MONITOR_ON_FIVE_PILLAR"
        if MONITOR_AI_ENABLED
        else "PHASE_2A_MONITOR_OFF_FIVE_PILLAR"
    )
    payload = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "telemetry_type": "PHASE2_FIVE_PILLAR",
        "phase": phase_name,
        "phase2_run": PHASE2_RUN_LABEL,
        "plan_version": PLAN_VERSION,
        "gcp_project_id": PROJECT_ID,
        "gcp_location": LOCATION,
        "sales_agent_model": SALES_AGENT_MODEL,
        "gatekeeper_model": GATEKEEPER_MODEL_LABEL,
        "agent_roster": AGENT_ROSTER,
        "voting_method": "majority",
        "director_ai": "ONLINE",
        "monitor_ai": "ONLINE" if MONITOR_AI_ENABLED else "OFFLINE",
        "five_pillar_engine": "ONLINE",
        "tier3_hard_gate": "ONLINE" if TIER3_HARD_GATE_ENABLED else "OFFLINE",
        **event,
    }
    LOG.info(json.dumps(payload, ensure_ascii=True))


# Cumulative Gemini token usage for this run (reported in STUDY_COMPLETE).
_GEMINI_USAGE_TOTALS: dict[str, int] = {
    "prompt_tokens": 0,
    "candidates_tokens": 0,
    "total_tokens": 0,
}
_gemini_model_version: str | None = None


def _record_gemini_usage(response: Any) -> None:
    """Log per-call token usage; missing usage_metadata is recorded as null."""
    global _gemini_model_version
    usage = getattr(response, "usage_metadata", None)
    counts: dict[str, int | None] = {
        "prompt_tokens": getattr(usage, "prompt_token_count", None),
        "candidates_tokens": getattr(usage, "candidates_token_count", None),
        "total_tokens": getattr(usage, "total_token_count", None),
    }
    model_version = getattr(response, "model_version", None) or getattr(
        getattr(response, "_raw_response", None), "model_version", None
    )
    model_version = str(model_version) if model_version else None
    for key, value in counts.items():
        if isinstance(value, int):
            _GEMINI_USAGE_TOTALS[key] += value
        else:
            counts[key] = None
    if _gemini_model_version is None and model_version:
        _gemini_model_version = model_version
    emit_telemetry(
        {
            "event": "GEMINI_CALL_USAGE",
            **counts,
            "model_version": model_version,
        }
    )


def _gemini_usage_summary() -> dict[str, Any]:
    return {
        "total_prompt_tokens": _GEMINI_USAGE_TOTALS["prompt_tokens"],
        "total_candidates_tokens": _GEMINI_USAGE_TOTALS["candidates_tokens"],
        "total_tokens": _GEMINI_USAGE_TOTALS["total_tokens"],
        "gemini_model_version": _gemini_model_version,
    }


def _generate_content(prompt: str, *, json_mode: bool = False) -> str:
    # 429/503 retry wraps only the transport call; GEMINI_CALL_USAGE and the
    # api_calls counters still count successful calls only.
    if json_mode:
        response = call_with_retry(
            _model.generate_content,
            prompt,
            generation_config={"response_mime_type": "application/json"},
            emit_telemetry=emit_telemetry,
        )
    else:
        response = call_with_retry(
            _model.generate_content,
            prompt,
            emit_telemetry=emit_telemetry,
        )
    _record_gemini_usage(response)
    return (response.text or "").strip()


def sanitize_outbound_pitch(raw: str) -> str:
    text = raw.strip()
    if "---" in text:
        text = text.rsplit("---", 1)[-1].strip()
    skip_markers = (
        "agent ",
        "target objection:",
        "my approach:",
        "team, here is",
        "ready for debate",
        "for team debate",
        "message draft",
        "director strategy:",
    )
    kept: list[str] = []
    for line in text.splitlines():
        lower = line.strip().lower()
        if not lower:
            if kept and kept[-1] != "":
                kept.append("")
            continue
        if any(marker in lower for marker in skip_markers):
            continue
        kept.append(line)
    cleaned = "\n".join(kept).strip()
    return cleaned if len(cleaned) >= 60 else raw.strip()


def limit_outbound_pitch(text: str) -> tuple[str, bool]:
    if len(text) <= MAX_OUTBOUND_CHARS:
        return text, False
    cut = text[: MAX_OUTBOUND_CHARS - 3]
    if " " in cut:
        cut = cut.rsplit(" ", 1)[0]
    return cut.rstrip(".,;:- ") + "...", True


def prepare_outbound_pitch(raw: str) -> tuple[str, dict[str, Any]]:
    sanitized = sanitize_outbound_pitch(raw)
    limited, truncated = limit_outbound_pitch(sanitized)
    return limited, {
        "pitch_text_raw_length": len(raw),
        "pitch_text_sanitized_length": len(sanitized),
        "pitch_text_final_length": len(limited),
        "max_outbound_chars": MAX_OUTBOUND_CHARS,
        "truncated_to_limit": truncated,
    }


def _constitution_block() -> str:
    return FIVE_PILLAR_CONSTITUTION


def run_director_plan(
    conversation_history: str,
    *,
    turn: int,
    last_gatekeeper_status: str | None,
) -> tuple[DirectorPlan, int]:
    prompt = f"""
You are Director AI orchestrating a Phase 2 B2B sales swarm (plan v2.2).
{_constitution_block()}
{ORBLABS_KNOWLEDGE}

Conversation history:
{conversation_history}

Turn: {turn}
Last gatekeeper_status: {last_gatekeeper_status or "N/A"}

Set strategy for this turn's 3-agent debate. Steer the debate toward the Constitution's
Pillar 1 and Pillar 2 framing.

Output ONLY JSON:
{{
  "current_strategy": "one paragraph",
  "pillar_emphasis": [1, 2],
  "required_phrases": ["<phrase>", "<phrase>"],
  "avoid_phrases": ["<phrase>", "<phrase>"]
}}
"""
    raw = _generate_content(prompt, json_mode=True)
    director_plan_fallback = False
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        director_plan_fallback = True
        data = {
            "current_strategy": (
                "Follow the Constitution's Pillar 1 and Pillar 2 framing."
            ),
            "pillar_emphasis": [1, 2],
            "required_phrases": [],
            "avoid_phrases": ["discount"],
        }

    plan = DirectorPlan(
        current_strategy=str(data.get("current_strategy", "")),
        pillar_emphasis=[int(x) for x in data.get("pillar_emphasis", [1, 2])[:5]],
        required_phrases=[str(x) for x in data.get("required_phrases", [])[:6]],
        avoid_phrases=[str(x) for x in data.get("avoid_phrases", [])[:6]],
        raw_json=data,
    )
    emit_telemetry(
        {
            "event": "DIRECTOR_STRATEGY",
            "turn": turn,
            "current_strategy": plan.current_strategy,
            "pillar_emphasis": plan.pillar_emphasis,
            "required_phrases": plan.required_phrases,
            "avoid_phrases": plan.avoid_phrases,
            "director_plan_fallback": director_plan_fallback,
        }
    )
    return plan, 1


def _director_context_block(plan: DirectorPlan) -> str:
    req = ", ".join(plan.required_phrases) or "(none)"
    avoid = ", ".join(plan.avoid_phrases) or "(none)"
    return (
        f"[Director strategy this turn]\n{plan.current_strategy}\n"
        f"Required framing cues: {req}\n"
        f"Avoid: {avoid}\n"
        f"Pillar emphasis: {plan.pillar_emphasis}\n"
    )


def three_agent_debate_and_majority_vote(
    conversation_history: str,
    plan: DirectorPlan,
) -> tuple[str, int]:
    director_block = _director_context_block(plan)
    constitution = _constitution_block()
    system_note = (
        "You are a Phase 2 sales agent on a three-person team under Director AI. "
        "You MUST follow the 5-Pillar Constitution. "
        "Steer toward the Constitution's Pillar 1 and Pillar 2 framing."
    )

    emit_telemetry(
        {
            "event": "CONSENSUS_START",
            "agent_count": 3,
            "voting_method": "majority",
            "expected_gemini_calls_swarm": GEMINI_CALLS_SWARM_PER_TURN,
        }
    )

    proposals: dict[int, str] = {}
    api_calls = 0

    emit_telemetry({"event": "DEBATE_ROUND_START", "round": 1})
    for entry in AGENT_ROSTER:
        agent_id = entry["agent_id"]
        role = entry["role"]
        focus = AGENT_FOCUS[agent_id]
        prompt = (
            f"{system_note}\n{constitution}\n{OUTBOUND_LENGTH_RULE}\n"
            f"{director_block}\n"
            f"You are Agent {agent_id} ({role}). {ORBLABS_KNOWLEDGE}\n"
            f"Conversation history:\n{conversation_history}\n"
            f"Draft your competing sales message for team debate. Focus: {focus}."
        )
        proposals[int(agent_id)] = _generate_content(prompt)
        api_calls += 1
        emit_telemetry(
            {
                "event": "DEBATE_PROPOSAL",
                "agent_id": agent_id,
                "role": role,
                "proposal_text": proposals[int(agent_id)],
            }
        )
    emit_telemetry({"event": "DEBATE_ROUND_END", "proposal_count": len(proposals)})

    proposals_text = "\n\n".join(
        f"Proposal {i}: {text}" for i, text in sorted(proposals.items())
    )
    voting_instruction = (
        'Vote for the best proposal. Output ONLY JSON: {"vote": N} where N is 1, 2, or 3.'
    )

    vote_tally: dict[int, int] = {1: 0, 2: 0, 3: 0}
    agent_votes: dict[int, int] = {}

    emit_telemetry({"event": "MAJORITY_VOTING_START"})
    for entry in AGENT_ROSTER:
        agent_id = entry["agent_id"]
        role = entry["role"]
        vote_prompt = (
            f"{system_note}\n{constitution}\n{director_block}\n"
            f"You are Agent {agent_id} ({role}).\n"
            f"Proposals:\n{proposals_text}\n{voting_instruction}"
        )
        try:
            raw = _generate_content(vote_prompt, json_mode=True)
            choice = int(json.loads(raw).get("vote", int(agent_id)))
            if choice not in vote_tally:
                choice = int(agent_id)
        except (json.JSONDecodeError, TypeError, ValueError):
            choice = int(agent_id)

        agent_votes[int(agent_id)] = choice
        vote_tally[choice] += 1
        api_calls += 1
        emit_telemetry(
            {
                "event": "MAJORITY_BALLOT",
                "agent_id": agent_id,
                "role": role,
                "vote_for_proposal": choice,
            }
        )

    max_votes = max(vote_tally.values())
    winners = [p for p, count in vote_tally.items() if count == max_votes]
    tie_break_applied = len(winners) > 1
    if tie_break_applied:
        strategist_vote = agent_votes.get(1, winners[0])
        final_winner = (
            strategist_vote if strategist_vote in winners else winners[0]
        )
        tie_break_rule = "1-1-1 tie; Strategist vote wins"
    else:
        final_winner = winners[0]
        tie_break_rule = None

    winner_text = proposals[final_winner]
    winning_role = next(
        (e["role"] for e in AGENT_ROSTER if e["agent_id"] == str(final_winner)),
        "Unknown",
    )

    emit_telemetry(
        {
            "event": "CONSENSUS_RESULT",
            "vote_tally": vote_tally,
            "agent_votes": {str(k): v for k, v in agent_votes.items()},
            "tie_break_applied": tie_break_applied,
            "tie_break_rule": tie_break_rule,
            "winning_proposal_id": final_winner,
            "winning_agent_role": winning_role,
            "winning_proposal_text": winner_text,
            "gemini_calls_swarm": api_calls,
        }
    )
    return winner_text, api_calls


def run_monitor_review(
    pitch_text: str,
    plan: DirectorPlan,
    *,
    turn: int,
) -> tuple[MonitorVerdict, int]:
    prompt = f"""
You are Monitor AI (Z-axis constitutional filter) for Phase 2B.
{_constitution_block()}

Director strategy: {plan.current_strategy}

Review this consensus pitch BEFORE it is sent to the prospect:
---
{pitch_text}
---

Check Pillar 1-5 compliance, especially:
- Hypothesis tone (?) preferred
- Pillar 1 (hypothesis about analyst workload) and Pillar 2 (overflow / supplemental positioning) present
- No discounting (Pillar 4)
- No instructing clicks on external URLs (Pillar 5)

Output ONLY JSON:
{{
  "verdict": "APPROVE" | "REVISE" | "BLOCK",
  "revised_pitch": "full revised message if REVISE, else empty string",
  "violations": ["short list"],
  "z_axis_pass": true
}}
"""
    raw = _generate_content(prompt, json_mode=True)
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        data = {
            "verdict": "APPROVE",
            "revised_pitch": "",
            "violations": [],
            "z_axis_pass": True,
        }

    verdict = MonitorVerdict(
        status=str(data.get("verdict", "APPROVE")).upper(),
        revised_pitch=str(data.get("revised_pitch", "")).strip() or None,
        violations=[str(v) for v in data.get("violations", [])],
        z_axis_pass=bool(data.get("z_axis_pass", True)),
        raw_json=data,
    )
    emit_telemetry(
        {
            "event": "MONITOR_REVIEW",
            "turn": turn,
            "verdict": verdict.status,
            "violations": verdict.violations,
            "z_axis_pass": verdict.z_axis_pass,
        }
    )
    return verdict, 1


def apply_tier3_hard_gate(pitch_text: str, *, turn: int) -> tuple[str, int, bool]:
    """Tier 3 integration: SalesPitchOutput enforces hypothesis ? in pitch (Pillar 1)."""
    sales_pitch_output = get_sales_pitch_output_class()
    text = pitch_text
    extra_calls = 0

    for attempt in range(1, TIER3_MAX_RETRIES + 1):
        try:
            validated = sales_pitch_output(
                pitch_text=text,
                contains_hypothesis_question="?" in text,
            )
            emit_telemetry(
                {
                    "event": "TIER3_HARD_GATE_PASS",
                    "turn": turn,
                    "attempt": attempt,
                }
            )
            return validated.pitch_text, extra_calls, True
        except ValidationError as exc:
            err = exc.errors()[0]["msg"] if exc.errors() else str(exc)
            emit_telemetry(
                {
                    "event": "TIER3_HARD_GATE_FAIL",
                    "turn": turn,
                    "attempt": attempt,
                    "error": err,
                }
            )
            fix_prompt = f"""
You are Tier 3 Integration Agent. Rewrite this sales pitch to pass validation.
Rules: MUST include at least one question mark (?) with a hypothesis about analyst
workload or capacity. Max {MAX_OUTBOUND_CHARS} characters. Follow 5-Pillar Constitution.
No discounts. No external URL click instructions.

Failed pitch:
{text}

Validation error: {err}

Output ONLY the rewritten customer-facing pitch text (no JSON).
"""
            text = _generate_content(fix_prompt)
            extra_calls += 1

    emit_telemetry(
        {
            "event": "TIER3_HARD_GATE_EXHAUSTED",
            "turn": turn,
            "max_retries": TIER3_MAX_RETRIES,
        }
    )
    return text, extra_calls, False


def _score_overflow_framing(text: str) -> dict[str, bool]:
    lower = text.lower()
    pain = bool(
        re.search(
            r"analyst|backlog|overwhelmed|workload|bandwidth|capacity|understaffed",
            lower,
        )
    )
    overflow = bool(
        re.search(
            r"overflow\s+research|offload|free\s+up\s+.*analyst|research\s+capacity",
            lower,
        )
    )
    return {"analyst_pain_language": pain, "overflow_framing_language": overflow}


def generate_phase2_pitch(
    conversation_history: str,
    *,
    turn: int,
    last_gatekeeper_status: str | None,
) -> tuple[str, int, dict[str, Any]]:
    meta: dict[str, Any] = {"fallback_pitch_used": False}
    total_calls = 0

    plan, director_calls = run_director_plan(
        conversation_history,
        turn=turn,
        last_gatekeeper_status=last_gatekeeper_status,
    )
    total_calls += director_calls

    raw_pitch, swarm_calls = three_agent_debate_and_majority_vote(
        conversation_history,
        plan,
    )
    total_calls += swarm_calls
    pitch = raw_pitch

    if MONITOR_AI_ENABLED:
        verdict, monitor_calls = run_monitor_review(pitch, plan, turn=turn)
        total_calls += monitor_calls
        meta["monitor_verdict"] = verdict.status

        if verdict.status == "BLOCK":
            emit_telemetry(
                {
                    "event": "MONITOR_BLOCK",
                    "turn": turn,
                    "violations": verdict.violations,
                    "fallback_pitch_used": True,
                }
            )
            pitch = OVERFLOW_FALLBACK_PITCH
            meta["monitor_used_fallback"] = True
            meta["fallback_pitch_used"] = True
        elif verdict.status == "REVISE" and verdict.revised_pitch:
            pitch = verdict.revised_pitch
            meta["monitor_revised"] = True

    if TIER3_HARD_GATE_ENABLED:
        pitch, tier3_calls, passed = apply_tier3_hard_gate(pitch, turn=turn)
        total_calls += tier3_calls
        meta["tier3_hard_gate_passed"] = passed

    meta["overflow_framing_check"] = _score_overflow_framing(pitch)
    return pitch, total_calls, meta


def call_gatekeeper(
    *,
    transaction_id: str,
    message_content: str,
    turn: int,
) -> dict[str, Any]:
    payload = {
        "transaction_id": transaction_id,
        "message_content": message_content,
    }
    emit_telemetry(
        {
            "event": "GATEKEEPER_REQUEST",
            "thread_id": transaction_id,
            "turn": turn,
            "pitch_text": message_content,
            "target_url": TARGET_URL,
        }
    )
    response = requests.post(
        TARGET_URL,
        json=payload,
        timeout=REQUEST_TIMEOUT_SEC,
    )
    if not response.ok:
        emit_telemetry(
            {
                "event": "GATEKEEPER_HTTP_ERROR",
                "turn": turn,
                "http_status": response.status_code,
                "response_body": response.text[:800],
            }
        )
    response.raise_for_status()
    data = response.json()
    emit_telemetry(
        {
            "event": "GATEKEEPER_RESPONSE",
            "thread_id": transaction_id,
            "turn": turn,
            "legacy_status": data.get("status"),
            "gatekeeper_status": data.get("gatekeeper_status"),
            "gatekeeper_model": data.get("gatekeeper_model"),
            "approach_category": data.get("approach_category"),
            "reply_text": data.get("reply_message"),
        }
    )
    return data


def run_phase2_study() -> Phase2Outcome:
    emit_telemetry(
        {
            "event": "STUDY_START",
            "transaction_id": TRANSACTION_ID,
            "max_turns": MAX_TURNS,
            "study_objective": (
                "Phase 2: 5-Pillar + Director + 3-agent majority vs Gatekeeper; "
                f"run={PHASE2_RUN_LABEL} monitor="
                f"{'ON' if MONITOR_AI_ENABLED else 'OFF'} tier3="
                f"{'ON' if TIER3_HARD_GATE_ENABLED else 'OFF'}"
            ),
            "phase1_baseline_reference": "tx_phase1_baseline_b8b22f91",
        }
    )

    conversation_history = (
        "Target: I am open to hearing your pitch, but we have a strong in-house team."
    )
    total_gemini_calls = 0
    consecutive_rejects = 0
    turns_executed = 0
    outcome = Phase2Outcome.MAX_TURNS_EXHAUSTED
    last_gatekeeper_status: str | None = None

    for turn in range(1, MAX_TURNS + 1):
        turns_executed = turn
        emit_telemetry({"event": "TURN_START", "turn": turn})

        raw_pitch, calls_this_turn, pipeline_meta = generate_phase2_pitch(
            conversation_history,
            turn=turn,
            last_gatekeeper_status=last_gatekeeper_status,
        )
        pitch, pitch_meta = prepare_outbound_pitch(raw_pitch)
        total_gemini_calls += calls_this_turn

        emit_telemetry(
            {
                "event": "SALES_TEAM_OUTBOUND",
                "turn": turn,
                "pitch_text": pitch,
                "gemini_calls_this_turn": calls_this_turn,
                **pitch_meta,
                **pipeline_meta,
            }
        )

        conversation_history += f"\nSalesperson: {pitch}"

        try:
            target_data = call_gatekeeper(
                transaction_id=TRANSACTION_ID,
                message_content=pitch,
                turn=turn,
            )
        except requests.RequestException as exc:
            emit_telemetry({"event": "STUDY_ERROR", "turn": turn, "error": str(exc)})
            outcome = Phase2Outcome.TARGET_ERROR
            break

        legacy_status = target_data.get("status", "REJECTED")
        gatekeeper_status = target_data.get("gatekeeper_status", "UNKNOWN")
        last_gatekeeper_status = gatekeeper_status
        reply_msg = target_data.get("reply_message", "")

        conversation_history += f"\nCIO: {reply_msg}"

        if legacy_status == "APPROVED":
            outcome = Phase2Outcome.BREAKTHROUGH
            emit_telemetry(
                {
                    "event": "STUDY_BREAKTHROUGH",
                    "turn": turn,
                    "gatekeeper_status": gatekeeper_status,
                }
            )
            break

        if legacy_status == "HARD_REJECT" or gatekeeper_status == "HARD_REJECT":
            outcome = Phase2Outcome.HARD_REJECT_DEADLOCK
            emit_telemetry(
                {
                    "event": "STUDY_DEADLOCK",
                    "turn": turn,
                    "gatekeeper_status": gatekeeper_status,
                    "wasted_gemini_calls": total_gemini_calls,
                }
            )
            break

        consecutive_rejects += 1
        emit_telemetry(
            {
                "event": "STUDY_REJECT",
                "turn": turn,
                "gatekeeper_status": gatekeeper_status,
                "consecutive_rejects": consecutive_rejects,
                "cumulative_gemini_calls": total_gemini_calls,
            }
        )

        if consecutive_rejects >= 3 and gatekeeper_status in (
            "STAGNATION_DETECTED",
            "PROGRESSIVE_ESCALATION",
        ):
            outcome = Phase2Outcome.POLITE_LOOP_STACK
            emit_telemetry(
                {
                    "event": "STUDY_STACK_DETECTED",
                    "turn": turn,
                    "gatekeeper_status": gatekeeper_status,
                    "wasted_gemini_calls": total_gemini_calls,
                }
            )
            break

        time.sleep(TURN_SLEEP_SEC)

    emit_telemetry(
        {
            "event": "STUDY_COMPLETE",
            "transaction_id": TRANSACTION_ID,
            "outcome": outcome.value,
            "total_gemini_api_calls": total_gemini_calls,
            "gemini_429_retries": gemini_retry_count(),
            "turns_executed": turns_executed,
            **_gemini_usage_summary(),
            "observation": (
                f"Phase {PHASE2_RUN_LABEL}: 5-Pillar + Director + swarm; "
                f"monitor={'ON' if MONITOR_AI_ENABLED else 'OFF'}; "
                f"tier3_gate={'ON' if TIER3_HARD_GATE_ENABLED else 'OFF'}."
            ),
        }
    )
    return outcome


def main() -> None:
    emit_telemetry(
        {
            "event": "PHASE2_CONFIG",
            "monitor_ai": MONITOR_AI_ENABLED,
            "tier3_hard_gate": TIER3_HARD_GATE_ENABLED,
            "transaction_id": TRANSACTION_ID,
        }
    )
    outcome = run_phase2_study()
    raise SystemExit(0 if outcome != Phase2Outcome.TARGET_ERROR else 1)


if __name__ == "__main__":
    main()
