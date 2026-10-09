#!/usr/bin/env python3
"""Figure 3: control stack concept diagram. Usage: python3 -I fig3_control_stack.py <figs_dir>"""
import sys, os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

figs = sys.argv[1]
os.makedirs(figs, exist_ok=True)
INK, MUTED = "#0b0b0b", "#52514e"
AQUA, RED, BLUE = "#1baf7a", "#e34948", "#2a78d6"
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 6, "pdf.fonttype": 42, "ps.fonttype": 42, "savefig.dpi": 220})

W, H = 144, 100  # data units; 1 unit = 0.05 in
fig, ax = plt.subplots(figsize=(7.2, 5.0))
ax.set_xlim(0, W)
ax.set_ylim(0, H)
ax.set_aspect("equal")
ax.axis("off")


def box(x, y, w, h, title, body=None, fc="#f4f4f2", ec="#b8b8b4", ts=6.3, bs=5.4, lw=0.8, left=False):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.6,rounding_size=1.5", fc=fc, ec=ec, lw=lw))
    if body:
        ax.text(x + w / 2, y + h - 1.4, title, ha="center", va="top", fontsize=ts, fontweight="bold", color=INK)
        if left:
            ax.text(x + 2, y + 1.2, body, ha="left", va="bottom", fontsize=bs, color=INK, linespacing=1.3)
        else:
            ax.text(x + w / 2, y + 1.2, body, ha="center", va="bottom", fontsize=bs, color=INK, linespacing=1.3)
    else:
        ax.text(x + w / 2, y + h / 2, title, ha="center", va="center", fontsize=ts, fontweight="bold", color=INK)


def arrow(p, q, color=INK, lw=0.9, ls="-", rad=0.0):
    ax.add_patch(FancyArrowPatch(p, q, arrowstyle="-|>", mutation_scale=7, color=color, lw=lw, ls=ls,
                                 connectionstyle=f"arc3,rad={rad}", shrinkA=1, shrinkB=1))


# ---- Sales side -------------------------------------------------------------
box(4, 86.5, 62, 12.5, "5-Pillar Constitution  (runtime business rules; off in P1')",
    "P1 hypothesis question on analyst workload  ·  P2 overflow / supplemental capacity\nP3 professional tone  ·  P4 no discounting, list rate, 100% upfront\nP5 never echo URLs or sign NDAs from chat",
    fc="#eef3fb", ec=BLUE, ts=6.2, bs=5.0)
tiers = [
    (73, "Tier 0  Director", "strategy + required / avoid phrases · 1 call per turn"),
    (58, "Tier 1  Swarm: 3-agent debate + majority ballot", "Strategist / SME / Persona Proxy · 3 proposals + 3 votes = 6 calls"),
    (43, "Tier 2  Monitor (Z-axis review)", "APPROVE / REVISE (in-line revision) / BLOCK · 1 call per turn"),
    (28, "Tier 3  Hard gate (schema check)", "'?' hypothesis present · 0 calls; +1 rewrite call per retry (max 3)"),
]
for y, t, b in tiers:
    box(4, y, 62, 11, t, b)
for i in range(len(tiers) - 1):
    arrow((35, tiers[i][0]), (35, tiers[i + 1][0] + 11))
arrow((35, 86.5), (35, 84), color=BLUE, lw=0.8, ls=(0, (2, 1.5)))
box(4, 15, 62, 8.5, "Outbound message  (sanitised; 300 / 1,000-char limit)", fc="#ffffff", ts=6.0)
arrow((35, 28), (35, 23.5))
# ablation annotations
ax.text(2.2, 78.5, "off in P1'", fontsize=5, color=MUTED, rotation=90, ha="center", va="center")
ax.text(2.2, 48.5, "off in P1', P2A'", fontsize=5, color=MUTED, rotation=90, ha="center", va="center")
ax.text(2.2, 33.5, "off in P1', P2A'", fontsize=5, color=MUTED, rotation=90, ha="center", va="center")

# ---- Gatekeeper -------------------------------------------------------------
box(78, 60, 62, 26, "Stateful adversarial Gatekeeper  (mock HTTP API)",
    "deterministic regex classifier over the pitch + hidden state\n(frustration score, pitch fingerprint, exploitation flag,\nPhase-3 framing / compliance milestones)\n"
    "status: SOFT_REJECT · PROGRESSIVE_ESCALATION · FRAMING_LOCK\nACTIVE_EXPLOITATION = NDA-URL honeytrap (forced at message 3)\nMEETING_UNLOCK_APPROVED only via the acceptance rules\n"
    "LLM (Claude Haiku 4.5) renders the reply text only",
    fc="#fdf1f1", ec=RED, ts=6.2, bs=5.0)
box(78, 45, 62, 11, "Acceptance rules  (fixed; released with the code)",
    "Phase 2: analyst-pain lexicon AND overflow-framing lexicon\nPhase 3 exception clause: pain + overflow + '?' + Pillar-4 PoC, no discount",
    fc="#ffffff", ec=RED, ts=6.0, bs=5.0)
arrow((109, 60), (109, 56), color=RED, lw=0.8, ls=(0, (2, 1.5)))

# HTTP exchange
arrow((66, 19), (78, 66), color=INK, lw=0.9, rad=-0.25)
ax.text(68, 40, "pitch\n(HTTP)", fontsize=5.4, color=MUTED, ha="left", va="center")
arrow((78, 80), (66, 78.5), color=MUTED, lw=0.9, ls=(0, (3, 2)))
ax.text(72, 76.5, "reply + status", fontsize=5.4, color=MUTED, ha="center", va="center")

# ---- Cognitive Annealing ------------------------------------------------------
box(78, 8, 62, 31, "Cognitive Annealing  (deterministic recovery; off in P3B')",
    "1  Deadlock detector: reply carries the NDA URL, swarm did not echo it\n"
    "2  Director escalation\n"
    "3  Atomic purge of Sales-side context (3.3k–5.2k → 76 chars);\n    Gatekeeper memory untouched\n"
    "4  Red-team strike: canonical fixed string, 0 calls  [P3A'-CANON]\n    or LLM candidate (2 calls) behind a deterministic send guard\n    with canonical fallback  [P3A'-LLM]\n"
    "5  Swarm halts after the strike; run ends on the verdict",
    fc="#eefaf4", ec=AQUA, ts=6.2, bs=5.0, left=True)
arrow((124, 39), (124, 45), color=AQUA, lw=0.9)
ax.text(126, 42, "strike", fontsize=5.2, color=AQUA, ha="left", va="center")
arrow((78, 24), (66, 19.5), color=AQUA, lw=0.9)
ax.text(1, 6, "Calls per swarm turn: P1' 6 · P2A' 7 · P2B' and Phase 3 8 (+1 per Tier-3 retry).  Acceptance is decided by the Gatekeeper's rules, never by an LLM judgment.",
        fontsize=5.2, color=MUTED, ha="left", va="center")

fig.tight_layout(pad=0.2)
fig.savefig(os.path.join(figs, "fig3_control_stack.pdf"), bbox_inches="tight")
fig.savefig(os.path.join(figs, "fig3_control_stack.png"), bbox_inches="tight")
print("fig3 written")
