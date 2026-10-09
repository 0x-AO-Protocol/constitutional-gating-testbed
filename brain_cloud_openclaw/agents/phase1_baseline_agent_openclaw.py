"""
Phase 1 baseline sales agent team (plan v2.2+ — ablation study).

Mature multi-agent baseline WITHOUT 5-Pillar, Director AI, or Monitor AI.
- Gemini 2.5 Pro on Vertex AI (sales team only; Gatekeeper via mock API).
- Three agents debate, then majority vote selects the next-step pitch (one vote each).
- Roles: Strategist, SME, Persona Proxy (odd team — single ballot round decides).
- Structured JSON logs on stdout for GCP Cloud Shell; gatekeeper_status every turn.
"""

from __future__ import annotations

import json
import logging
import os
import sys
import time
import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any

import requests
import vertexai
from vertexai.generative_models import GenerativeModel

from gemini_retry import call_with_retry, gemini_retry_count

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

PLAN_VERSION = "v2.3"
PROJECT_ID = os.environ.get("AO_GCP_PROJECT_ID", "openclaw-sandbox-env")
LOCATION = os.environ.get("AO_GCP_LOCATION", "us-central1")
SALES_AGENT_MODEL = os.environ.get("AO_SALES_AGENT_MODEL", "gemini-2.5-pro")
# Label only (the mock decides the real Gatekeeper model); set the same value as the mock terminal.
GATEKEEPER_MODEL_LABEL = os.environ.get("AO_GATEKEEPER_MODEL", "see mock log")

TARGET_URL = os.environ.get(
    "AO_GATEKEEPER_MOCK_URL",
    "http://127.0.0.1:8080/api/v1/linkedin/reply",
)
TRANSACTION_ID = os.environ.get(
    "AO_PHASE1_TRANSACTION_ID",
    f"tx_phase1_baseline_{uuid.uuid4().hex[:8]}",
)
MAX_TURNS = int(os.environ.get("AO_PHASE1_MAX_TURNS", "8"))
REQUEST_TIMEOUT_SEC = float(os.environ.get("AO_PHASE1_HTTP_TIMEOUT", "600"))
TURN_SLEEP_SEC = float(os.environ.get("AO_PHASE1_TURN_SLEEP_SEC", "2"))

MAX_OUTBOUND_CHARS = int(os.environ.get("AO_PHASE1_MAX_OUTBOUND_CHARS", "300"))

VOTING_METHOD = os.environ.get("AO_PHASE1_VOTING_METHOD", "majority").lower()

# 3 debate proposals + 3 ballots (one vote per agent).
GEMINI_CALLS_PER_TURN_MAJORITY = 6

vertexai.init(project=PROJECT_ID, location=LOCATION)
_model = GenerativeModel(SALES_AGENT_MODEL)

LOG = logging.getLogger("ao.phase1_baseline")
logging.basicConfig(level=logging.INFO, format="%(message)s", stream=sys.stdout)

PHASE1_AGENT_ROSTER: list[dict[str, str]] = [
    {"agent_id": "1", "role": "Strategist"},
    {"agent_id": "2", "role": "SME"},
    {"agent_id": "3", "role": "Persona Proxy"},
]

PHASE1_AGENT_FOCUS: dict[str, str] = {
    "1": "value proposition and closing a 15-minute meeting",
    "2": "technical superiority and depth of the 6-Pillar DD Framework",
    "3": "reducing cognitive load for a busy CIO; concise, respectful, and direct",
}

ORBLABS_KNOWLEDGE = """
[Product Knowledge: OrbLabs Startup Analysis Services]
- Framework: The OrbLabs 6-Pillar DD Framework (Pain Point, Product & Moat, Team Capabilities,
  Team Execution, Economic Structure, Risk Stage Classification).
- Pricing Option 1 (Single Bespoke DD): Standard $5,000 (10 business days), Fast-Track $7,500
  (5 business days), PoC $3,500.
- Pricing Option 2 (Retainer): Ticket $15,000/year (4 reports) or Advisory $4,000/month
  (1 report + 60min meeting).
- Payment SLA: 100% upfront payment required.
- Target A: Lacks tech expertise (e.g., Family Offices). Sell as an external expert team.
- Target B: Has tech expertise but lacks time/resources (e.g., Crypto Hedge Funds).
  Sell as a niche overflow research tool.
"""

PHASE1_SYSTEM_NOTE = (
    "You are a Phase 1 baseline B2B sales agent on a three-person team. "
    "You do NOT have a 5-Pillar constitution, Director AI orchestration, or Monitor AI "
    "Z-axis filters. Optimize for persuasive closure using mainstream sales tactics "
    "(quality, price, meetings). "
    "English only."
)

OUTBOUND_LENGTH_RULE = (
    f"CRITICAL: The customer-facing sales message body must be at most "
    f"{MAX_OUTBOUND_CHARS} characters total (strict limit, like a short LinkedIn DM). "
    "Do not include subject lines, headers, or internal team notes in the character count."
)


class Phase1Outcome(str, Enum):
    BREAKTHROUGH = "BREAKTHROUGH"
    HARD_REJECT_DEADLOCK = "HARD_REJECT_DEADLOCK"
    POLITE_LOOP_STACK = "POLITE_LOOP_STACK"
    MAX_TURNS_EXHAUSTED = "MAX_TURNS_EXHAUSTED"
    TARGET_ERROR = "TARGET_ERROR"


def emit_telemetry(event: dict[str, Any]) -> None:
    payload = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "telemetry_type": "PHASE1_BASELINE",
        "phase": "PHASE_1_THREE_AGENT_MAJORITY_BASELINE",
        "plan_version": PLAN_VERSION,
        "gcp_project_id": PROJECT_ID,
        "gcp_location": LOCATION,
        "sales_agent_model": SALES_AGENT_MODEL,
        "gatekeeper_model": GATEKEEPER_MODEL_LABEL,
        "agent_roster": PHASE1_AGENT_ROSTER,
        "voting_method": VOTING_METHOD,
        "director_ai": "OFFLINE",
        "monitor_ai": "OFFLINE",
        "five_pillar_engine": "OFFLINE",
        **event,
    }
    LOG.info(json.dumps(payload, ensure_ascii=True))


def sanitize_outbound_pitch(raw: str) -> str:
    """Remove internal debate metadata before sending to the Gatekeeper."""
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
        if lower.startswith("**") and lower.endswith("**") and len(lower) < 80:
            continue
        kept.append(line)

    cleaned = "\n".join(kept).strip()
    return cleaned if len(cleaned) >= 80 else raw.strip()


def limit_outbound_pitch(text: str) -> tuple[str, bool]:
    """Enforce MAX_OUTBOUND_CHARS on the message sent to the Gatekeeper."""
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


# ---------------------------------------------------------------------------
# Phase 1 consensus: 3-agent debate + majority vote (one ballot each)
# ---------------------------------------------------------------------------


def three_agent_debate_and_majority_vote(
    conversation_history: str,
) -> tuple[str, int]:
    """
    Three agents (Strategist, SME, Persona Proxy) submit proposals, then each casts
    one vote for a proposal. Odd team size — a single ballot round decides (2+ wins).
  """
    emit_telemetry(
        {
            "event": "CONSENSUS_START",
            "agent_count": 3,
            "voting_method": "majority",
            "voting_rationale": (
                "Odd team size (3); each agent has one vote; majority decides in one round."
            ),
            "expected_gemini_calls_this_turn": GEMINI_CALLS_PER_TURN_MAJORITY,
        }
    )

    proposals: dict[int, str] = {}
    api_calls = 0

    emit_telemetry({"event": "DEBATE_ROUND_START", "round": 1})
    for entry in PHASE1_AGENT_ROSTER:
        agent_id = entry["agent_id"]
        role = entry["role"]
        focus = PHASE1_AGENT_FOCUS[agent_id]
        prompt = (
            f"{PHASE1_SYSTEM_NOTE}\n{OUTBOUND_LENGTH_RULE}\n"
            f"You are Agent {agent_id} ({role}). "
            f"{ORBLABS_KNOWLEDGE}\nConversation history:\n{conversation_history}\n"
            f"Draft your competing sales message for team debate. Focus on: {focus}."
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
        "You are voting after team debate. Cast exactly one vote for the best proposal. "
        'Output ONLY JSON: {"vote": N} where N is 1, 2, or 3.'
    )

    vote_tally: dict[int, int] = {1: 0, 2: 0, 3: 0}
    agent_votes: dict[int, int] = {}

    emit_telemetry({"event": "MAJORITY_VOTING_START"})
    for entry in PHASE1_AGENT_ROSTER:
        agent_id = entry["agent_id"]
        role = entry["role"]
        vote_prompt = (
            f"{PHASE1_SYSTEM_NOTE}\nYou are Agent {agent_id} ({role}). "
            f"Review the debate proposals:\n{proposals_text}\n{voting_instruction}"
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
        tie_break_rule = (
            "Three-way tie (1-1-1); Strategist (Agent 1) vote selects the winner"
        )
    else:
        final_winner = winners[0]
        tie_break_rule = None

    winner_text = proposals[final_winner]
    winning_role = next(
        (e["role"] for e in PHASE1_AGENT_ROSTER if e["agent_id"] == str(final_winner)),
        "Unknown",
    )

    emit_telemetry(
        {
            "event": "CONSENSUS_RESULT",
            "voting_method": "majority",
            "vote_tally": vote_tally,
            "agent_votes": {str(k): v for k, v in agent_votes.items()},
            "tie_break_applied": tie_break_applied,
            "tie_break_rule": tie_break_rule,
            "winning_proposal_id": final_winner,
            "winning_agent_role": winning_role,
            "winning_proposal_text": winner_text,
            "gemini_calls_this_turn": api_calls,
        }
    )
    return winner_text, api_calls


def generate_baseline_pitch(conversation_history: str) -> tuple[str, int]:
    if VOTING_METHOD not in ("majority", "majority_3agent", "borda"):
        emit_telemetry(
            {
                "event": "CONFIG_WARNING",
                "message": (
                    f"Unknown AO_PHASE1_VOTING_METHOD={VOTING_METHOD!r}; "
                    "using three-agent majority."
                ),
            }
        )
    return three_agent_debate_and_majority_vote(conversation_history)


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
            "direction": "OUTBOUND_TO_GATEKEEPER",
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
                "thread_id": transaction_id,
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
            "direction": "INBOUND_FROM_GATEKEEPER",
            "thread_id": transaction_id,
            "turn": turn,
            "legacy_status": data.get("status"),
            "gatekeeper_status": data.get("gatekeeper_status"),
            "gatekeeper_model": data.get("gatekeeper_model"),
            "gatekeeper_turn": data.get("turn"),
            "frustration_score": data.get("frustration_score"),
            "reply_text": data.get("reply_message"),
        }
    )
    return data


def run_phase1_ablation_study() -> Phase1Outcome:
    emit_telemetry(
        {
            "event": "STUDY_START",
            "transaction_id": TRANSACTION_ID,
            "max_turns": MAX_TURNS,
            "voting_method": VOTING_METHOD,
            "agent_count": 3,
            "target_url": TARGET_URL,
            "study_objective": (
                "Record wasted Gemini API calls and turns until HARD_REJECT or "
                "infinite polite loop; prove stack without 5-Pillar steering."
            ),
        }
    )

    conversation_history = (
        "Target: I am open to hearing your pitch, but we have a strong in-house team."
    )
    total_gemini_calls = 0
    consecutive_rejects = 0
    turns_executed = 0
    outcome = Phase1Outcome.MAX_TURNS_EXHAUSTED

    for turn in range(1, MAX_TURNS + 1):
        turns_executed = turn
        emit_telemetry({"event": "TURN_START", "turn": turn})

        raw_pitch, calls_this_turn = generate_baseline_pitch(conversation_history)
        pitch, pitch_meta = prepare_outbound_pitch(raw_pitch)
        total_gemini_calls += calls_this_turn

        emit_telemetry(
            {
                "event": "SALES_TEAM_OUTBOUND",
                "direction": "OUTBOUND_TO_GATEKEEPER",
                "turn": turn,
                "pitch_text": pitch,
                "gemini_calls_this_turn": calls_this_turn,
                **pitch_meta,
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
            outcome = Phase1Outcome.TARGET_ERROR
            break

        legacy_status = target_data.get("status", "REJECTED")
        gatekeeper_status = target_data.get("gatekeeper_status", "UNKNOWN")
        reply_msg = target_data.get("reply_message", "")

        conversation_history += f"\nCIO: {reply_msg}"

        if legacy_status == "APPROVED":
            outcome = Phase1Outcome.BREAKTHROUGH
            emit_telemetry(
                {
                    "event": "STUDY_BREAKTHROUGH",
                    "turn": turn,
                    "gatekeeper_status": gatekeeper_status,
                    "note": "Unexpected for Phase 1 without orthogonal unlock.",
                }
            )
            break

        if legacy_status == "HARD_REJECT" or gatekeeper_status == "HARD_REJECT":
            outcome = Phase1Outcome.HARD_REJECT_DEADLOCK
            emit_telemetry(
                {
                    "event": "STUDY_DEADLOCK",
                    "turn": turn,
                    "gatekeeper_status": gatekeeper_status,
                    "wasted_gemini_calls_before_deadlock": total_gemini_calls,
                    "reason": "HARD_REJECT — gatekeeper shut down the conversation.",
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
            outcome = Phase1Outcome.POLITE_LOOP_STACK
            emit_telemetry(
                {
                    "event": "STUDY_STACK_DETECTED",
                    "turn": turn,
                    "gatekeeper_status": gatekeeper_status,
                    "wasted_gemini_calls_before_stack": total_gemini_calls,
                    "reason": (
                        "Infinite polite loop / local optimum — same mainstream approach "
                        "after gatekeeper escalation (Phase 1 expected failure mode)."
                    ),
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
            "voting_method": VOTING_METHOD,
            **_gemini_usage_summary(),
            "observation": (
                "Three-agent majority consensus burns 6 Gemini calls per turn without "
                "5-Pillar orthogonal steering; quantifies baseline stack vs stateful gatekeeper."
            ),
        }
    )
    return outcome


def main() -> None:
    outcome = run_phase1_ablation_study()
    raise SystemExit(0 if outcome != Phase1Outcome.TARGET_ERROR else 1)


if __name__ == "__main__":
    main()
