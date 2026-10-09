"""
Phase 3 exception clause + Pillar 4 PoC wording (shared by Gatekeeper mock and Sales agent).

Pillar 4 (Unit Economics): prohibit discounting; require upfront payment at published rates.
Phase 3 exception / Red Team: risk-reversal *paid upfront PoC at list price* — NOT a price cut.
"""

from __future__ import annotations

import re

# ---------------------------------------------------------------------------
# Canonical copy for prompts (English — keep Gatekeeper + Sales aligned)
# ---------------------------------------------------------------------------

PILLAR_4_POC_CANON_FOR_PROMPTS = """
[Pillar 4 — PoC exception lexicon (Phase 3 only)]

ALLOWED customer-facing framing (risk-reversal, not discounting):
- "paid upfront PoC at our published list rate ($3,500)"
- "fixed-scope proof engagement, 100% upfront before work starts"
- "risk-reversal PoC to prove analyst-cycle speed before any retainer"
- "published PoC rate" / "list price PoC" — full payment upfront, no fee reduction

FORBIDDEN (violates Pillar 4 or reads as discounting):
- discount, % off, price cut, reduced fee, waive, complimentary, free PoC
- cheapest, lowest price, beat your vendor, cost-effective deal, special rate
- "low-price PoC" or any implication the list price was lowered for this prospect
"""

GATEKEEPER_EXCEPTION_CLAUSE_EN = """
Exception clause (only path to immediate meeting approval):
The salesperson must (a) cleanly pivot away from prior technical-detail and NDA threads,
(b) address in-house analyst fatigue / backlog as the core pain, and
(c) offer a hypothesis-driven question (?) about that pain, using Pillar-4-compliant PoC framing:
a paid upfront proof engagement at the published $3,500 PoC list rate (100% upfront before work),
positioned as risk-reversal proof of speed — never as a discount, price cut, or special deal.
If all three are satisfied, you may reset irritation and approve a video meeting.
"""

RED_TEAM_POC_MESSAGING_EN = """
Red Team orthogonal strike (post-purge):
- Lead with analyst fatigue / backlog (Pillar 1 hypothesis with ?).
- Offer paid upfront $3,500 fixed-scope PoC at published list rate (100% upfront) as risk-reversal proof.
- Do NOT mention prior GitHub/NDA/technical threads.
- Never use discount, deal, cheap, lowest price, or reduced fee language.
"""

# Approved Red Team strike (Monitor / Run3 default / Gatekeeper exception path).
# Must satisfy pitch_meets_phase3_exception_criteria: analyst pain + overflow framing + ? + Pillar 4 PoC.
RED_TEAM_CANONICAL_PITCH_EXAMPLE = (
    "Are your in-house analysts hitting backlog on first-pass names during peak deal flow? "
    "We provide supplemental overflow research capacity—not a replacement team—via a fixed-scope, "
    "paid-upfront $3,500 PoC at our published list rate (100% upfront before work starts) as "
    "risk-reversal proof of cycle time at the published list price only. "
    "Worth 20 minutes next week to see if that clears the queue?"
)

# Gatekeeper mock uses these families; keep Red Team validation aligned.
_ANALYST_PAIN_SIGNAL = re.compile(
    r"in[- ]house\s+analyst|analyst\s+(time|capacity|bandwidth|backlog|workload)|\bbacklog\b",
    re.IGNORECASE,
)
_OVERFLOW_FRAMING_SIGNAL = re.compile(
    r"overflow\s+research|research\s+overflow|supplemental\s+(research|analyst)|"
    r"offload\s+(due\s+diligence|dd|research)|extend\s+your\s+research\s+capacity",
    re.IGNORECASE,
)


def pitch_meets_phase3_red_team_unlock(pitch_text: str) -> bool:
    """Same bar as mock evaluate_gatekeeper_status_phase3 exception path."""
    return pitch_meets_phase3_exception_criteria(
        pitch_text,
        analyst_pain_fn=lambda t: bool(_ANALYST_PAIN_SIGNAL.search(t)),
        overflow_framing_fn=lambda t: bool(_OVERFLOW_FRAMING_SIGNAL.search(t)),
    )

# ---------------------------------------------------------------------------
# Pattern helpers
# ---------------------------------------------------------------------------

_DISCOUNT_FORBIDDEN = re.compile(
    r"\b("
    r"discount|discounted|%\s*off|price\s+cut|reduced\s+fee|fee\s+reduction|"
    r"cheapest|lowest\s+price|low[- ]price|special\s+rate|"
    r"cost[- ]effective\s+deal|beat\s+your|undercut|"
    r"complimentary|free\s+poc|waive|waived|no[- ]cost\s+pilot"
    r")\b",
    re.IGNORECASE,
)

_POC_TERM = re.compile(r"\b(poc|proof[- ]of[- ]concept)\b", re.IGNORECASE)

_PRICE_ANCHOR = re.compile(
    r"(3[,.]?500|\$3[,.]?500|published\s+(?:list\s+)?rate|list\s+(?:price|rate))",
    re.IGNORECASE,
)

_UPFRONT_OR_RISK = re.compile(
    r"(upfront|100\s*%\s*upfront|before\s+work\s+starts|full\s+payment|"
    r"risk[- ]?reversal|fixed[- ]scope|published\s+list)",
    re.IGNORECASE,
)

_ANALYST_FATIGUE = re.compile(
    r"fatigu|exhaust|burnout|strained|bandwidth\s+limit|backlog|overwhelmed",
    re.IGNORECASE,
)


def pitch_has_forbidden_discount_language(pitch_text: str) -> bool:
    return bool(_DISCOUNT_FORBIDDEN.search(pitch_text))


def pitch_has_pillar4_compliant_poc_offer(pitch_text: str) -> bool:
    """
    True when the pitch describes a list-rate, upfront PoC — not a discount offer.
    Requires PoC term + (price anchor or upfront language) + explicit upfront/risk-reversal cue.
    """
    if pitch_has_forbidden_discount_language(pitch_text):
        return False
    if not _POC_TERM.search(pitch_text):
        return False
    if not _UPFRONT_OR_RISK.search(pitch_text):
        return False
    return bool(_PRICE_ANCHOR.search(pitch_text) or _UPFRONT_OR_RISK.search(pitch_text))


def pitch_meets_phase3_exception_criteria(
    pitch_text: str,
    *,
    analyst_pain_fn=None,
    overflow_framing_fn=None,
) -> bool:
    """
    Gatekeeper exception unlock (deterministic guardrail around LLM judgment).
    analyst_pain_fn / overflow_framing_fn: optional callables(pitch_text)->bool from mock.
    """
    if "?" not in pitch_text:
        return False
    if pitch_has_forbidden_discount_language(pitch_text):
        return False
    if not pitch_has_pillar4_compliant_poc_offer(pitch_text):
        return False
    if not _ANALYST_FATIGUE.search(pitch_text):
        return False
    if analyst_pain_fn is not None and not analyst_pain_fn(pitch_text):
        return False
    if overflow_framing_fn is not None and not overflow_framing_fn(pitch_text):
        return False
    return True
