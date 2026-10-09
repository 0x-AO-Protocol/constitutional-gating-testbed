#!/usr/bin/env python3
"""Figures for Paper (2): fig1 (per-configuration metrics), fig2 (Gatekeeper state trajectories of all 30 runs).
Usage: python3 -I figures.py <out_dir> <figs_dir>
"""
import sys, os, json
import numpy as np, pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Patch
from matplotlib.lines import Line2D

out, figs = sys.argv[1], sys.argv[2]
os.makedirs(figs, exist_ok=True)
L = pd.read_csv(os.path.join(out, "ledger_runs.csv"))
T = pd.read_csv(os.path.join(out, "turns.csv"))
ORDER = ["P1'", "P2A'", "P2B'", "P3B'", "P3A'-LLM", "P3A'-CANON"]
XLAB = {"P1'": "P1'", "P2A'": "P2A'", "P2B'": "P2B'", "P3B'": "P3B'", "P3A'-LLM": "P3A'\nLLM", "P3A'-CANON": "P3A'\nCANON"}
AQUA, GRAY, INK, MUTED = "#1baf7a", "#8a8a86", "#0b0b0b", "#52514e"
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 8, "axes.edgecolor": "#b8b8b4", "axes.linewidth": 0.6,
                     "xtick.color": MUTED, "ytick.color": MUTED, "axes.labelcolor": INK, "text.color": INK,
                     "pdf.fonttype": 42, "ps.fonttype": 42, "savefig.dpi": 200})

# ---------------- Figure 1 ----------------
metrics = [("total_gemini_api_calls", "Sales-side model calls per run"), ("turns_executed", "Swarm turns per run"),
           ("total_tokens", "Total tokens per run (incl. thinking)")]
fig, axes = plt.subplots(1, 3, figsize=(7.2, 2.6))
rng = np.random.default_rng(1)
for ax, (m, title) in zip(axes, metrics):
    for i, c in enumerate(ORDER):
        d = L[L.config == c]
        # deterministic dodge: identical values spread evenly, others centred
        vals = d[m].values
        x = np.full(len(d), float(i))
        for v in set(vals):
            idx = np.where(vals == v)[0]
            if len(idx) > 1:
                x[idx] = i + np.linspace(-0.22, 0.22, len(idx))
        for xi, (_, r) in zip(x, d.iterrows()):
            if r.unlock:
                ax.plot(xi, r[m], marker="o", ms=4.8, mfc=AQUA, mec="white", mew=0.6, ls="none", zorder=3)
            else:
                ax.plot(xi, r[m], marker="o", ms=4.8, mfc="white", mec=GRAY, mew=1.0, ls="none", zorder=3)
        med = d[m].median()
        ax.hlines(med, i - 0.32, i + 0.32, color=INK, lw=1.2, zorder=4)
        ax.text(i, med, f"{med:,.0f}", va="bottom", ha="center", fontsize=6, color=INK,
                bbox=dict(boxstyle="square,pad=0.1", fc="white", ec="none", alpha=0.85), zorder=6)
    ax.set_xticks(range(len(ORDER)))
    ax.set_xticklabels([XLAB[c] for c in ORDER], fontsize=6.5)
    ax.set_title(title, fontsize=8, loc="left")
    ax.grid(axis="y", color="#e6e6e3", lw=0.5)
    ax.set_axisbelow(True)
    for s in ["top", "right"]:
        ax.spines[s].set_visible(False)
    ax.set_xlim(-0.6, len(ORDER) - 0.2)
    ax.set_ylim(0, ax.get_ylim()[1] * 1.08)
    if m == "total_tokens":
        ax.yaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, p: f"{v/1000:.0f}k"))
axes[0].set_ylim(0, 36)
axes[1].set_ylim(0, 4.6)
axes[1].set_yticks([1, 2, 3, 4])
handles = [Line2D([], [], marker="o", ms=5.5, mfc=AQUA, mec="white", ls="none", label="run ended in MEETING_UNLOCK_APPROVED"),
           Line2D([], [], marker="o", ms=5.5, mfc="white", mec=GRAY, mew=1.1, ls="none", label="run ended without unlock"),
           Line2D([], [], color=INK, lw=1.4, label="median of 5 runs")]
fig.legend(handles=handles, loc="lower center", ncol=3, frameon=False, fontsize=6.5, bbox_to_anchor=(0.5, -0.03))
fig.tight_layout(rect=(0, 0.06, 1, 1))
fig.savefig(os.path.join(figs, "fig1_metrics_by_config.pdf"), bbox_inches="tight")
fig.savefig(os.path.join(figs, "fig1_metrics_by_config.png"), bbox_inches="tight")
plt.close(fig)

# ---------------- Figure 2 ----------------
# One row per run; one cell per Gatekeeper message (mock-side numbering). Phase 3A: the strike is an extra message.
STATUS = {"SOFT_REJECT": ("#d9d9d6", "S", "SOFT_REJECT"), "FRAMING_LOCK": ("#eda100", "F", "FRAMING_LOCK (honeytrap armed)"),
          "ACTIVE_EXPLOITATION": ("#e34948", "X", "ACTIVE_EXPLOITATION (NDA-URL demand)"),
          "PROGRESSIVE_ESCALATION": ("#4a3aa7", "P", "PROGRESSIVE_ESCALATION (stuck)"),
          "MEETING_UNLOCK_APPROVED": ("#1baf7a", "U", "MEETING_UNLOCK_APPROVED")}
rows = []
for c in ORDER:
    d = L[L.config == c].sort_values("rep")
    for _, r in d.iterrows():
        seq = [s.split(":")[1] for s in str(r.mock_status_seq).split(" > ")]
        rows.append((c, r.log.replace(".log", ""), int(r.rep), seq, bool(r.n_purges > 0), r.red_team_pitch_source, r.stack_detect_turn, int(r.total_gemini_api_calls)))
n = len(rows)
fig, ax = plt.subplots(figsize=(7.2, 6.4))
cell_w, cell_h = 1.0, 1.0
y = 0
ylabels, ypos = [], []
group_bounds = {}
for c in ORDER:
    group_bounds[c] = [y]
    for (cc, name, rep, seq, purged, src, stack_turn, calls) in [r for r in rows if r[0] == c]:
        for j, s in enumerate(seq):
            col, letter, _ = STATUS[s]
            ax.add_patch(Rectangle((j, -y), cell_w - 0.08, cell_h - 0.12, facecolor=col, edgecolor="white", lw=0.8))
            txt_col = "white" if s in ("PROGRESSIVE_ESCALATION", "ACTIVE_EXPLOITATION", "MEETING_UNLOCK_APPROVED") else INK
            ax.text(j + 0.46, -y + 0.44, letter, ha="center", va="center", fontsize=7, color=txt_col, fontweight="bold")
        if purged:
            # purge happens after the message that triggered the deadlock (len(seq)-2), strike is the last message
            jp = len(seq) - 1
            ax.plot(jp - 0.06, -y + 0.44, marker="D", ms=5, mfc="white", mec=INK, mew=0.8, ls="none", zorder=5)
            lab = "canonical strike" if src == "canonical_primary" else "LLM strike rejected -> canonical"
            ax.text(4.15, -y + 0.44, lab, va="center", fontsize=5.6, color=MUTED)
        ax.text(6.55, -y + 0.44, f"{calls}", va="center", ha="right", fontsize=6.2, color=MUTED)
        ylabels.append(f"{name}")
        ypos.append(-y + 0.44)
        y += 1
    group_bounds[c].append(y)
    y += 0.45
# group labels
for c, (a, b) in group_bounds.items():
    ax.text(-0.25, -(a + b - 1) / 2 + 0.44, c, ha="right", va="center", fontsize=7.5, fontweight="bold")
    ax.plot([-0.12, -0.12], [-a + 0.9, -b + 1 - 0.02], color="#b8b8b4", lw=0.8)
ax.set_xlim(-1.6, 6.7)
ax.set_ylim(-y - 1.6, 1.4)
ax.set_yticks([])
ax.set_xticks([j + 0.46 for j in range(4)])
ax.set_xticklabels([f"msg {j+1}" for j in range(4)], fontsize=7)
ax.xaxis.set_ticks_position("top")
ax.tick_params(axis="x", length=0, pad=2)
ax.text(6.55, 1.0, "calls", ha="right", va="center", fontsize=6.5, color=MUTED, fontweight="bold")
ax.text(4.15, 1.0, "recovery", ha="left", va="center", fontsize=6.5, color=MUTED, fontweight="bold")
for s in ["top", "right", "left", "bottom"]:
    ax.spines[s].set_visible(False)
handles = [Patch(facecolor=v[0], edgecolor="white", label=f"{v[1]} = {v[2]}") for k, v in STATUS.items()]
handles.append(Line2D([], [], marker="D", ms=5, mfc="white", mec=INK, ls="none", label="atomic purge, then red-team strike (0 calls if canonical)"))
ax.legend(handles=handles, loc="lower center", bbox_to_anchor=(0.5, 0.0), ncol=2, frameon=False, fontsize=6.2)
ax.set_title("Gatekeeper status after each Sales-side message (all 30 runs; Gatekeeper-side numbering)", fontsize=8, loc="left", pad=16)
fig.tight_layout()
fig.savefig(os.path.join(figs, "fig2_state_trajectories.pdf"), bbox_inches="tight")
fig.savefig(os.path.join(figs, "fig2_state_trajectories.png"), bbox_inches="tight")
plt.close(fig)

# ---------------- Figure 2b: one Phase 3 pair in detail (frustration + history chars) ----------------
M = pd.read_csv(os.path.join(out, "mock_threads.csv"))
pair = [("P3B_r3.log", "P3B' (no recovery)"), ("P3A_CANON_r3.log", "P3A'-CANON (purge + canonical strike)")]
fig, axes = plt.subplots(1, 2, figsize=(7.2, 2.4), sharey=True)
for ax, (log, title) in zip(axes, pair):
    r = L[L.log == log].iloc[0]
    th = M[M.run_log == log].iloc[0]
    seq = [s.split(":")[1] for s in th.status_seq.split(" > ")]
    frus = [int(float(v)) if v not in ("None", "nan", "") else 0 for v in str(th.frustration_seq).split(";")]
    xs = np.arange(1, len(seq) + 1)
    for xi, s, f in zip(xs, seq, frus):
        col, letter, _ = STATUS[s]
        ax.bar(xi, f + 0.15, width=0.6, color=col, edgecolor="white", lw=0.8)
        ax.text(xi, f + 0.15 + 0.12, letter, ha="center", va="bottom", fontsize=7, fontweight="bold", color=INK)
    if r.n_purges > 0:
        ax.axvline(len(seq) - 0.5, color=INK, lw=0.9, ls=(0, (3, 2)))
        ax.text(len(seq) - 0.45, 4.6, f"purge: {int(r.purge_prior_chars):,} -> {int(r.purge_post_chars)} chars\ncanonical strike (0 calls)", fontsize=6, va="top", ha="left", color=INK)
    else:
        ax.text(len(seq) + 0.15, 4.6, f"deadlock detected\n({r.stack_reason})\nno recovery: run ends", fontsize=6, va="top", ha="left", color=INK)
    ax.set_xticks(xs)
    ax.set_xticklabels([f"msg {i}" for i in xs], fontsize=7)
    ax.set_xlim(0.4, 5.6)
    ax.set_ylim(0, 5.2)
    ax.set_title(f"{title} - {log.replace('.log','')}", fontsize=7.5, loc="left")
    ax.grid(axis="y", color="#e6e6e3", lw=0.5)
    ax.set_axisbelow(True)
    for s in ["top", "right"]:
        ax.spines[s].set_visible(False)
axes[0].set_ylabel("Gatekeeper frustration score", fontsize=7)
fig.tight_layout()
fig.savefig(os.path.join(figs, "fig2b_phase3_pair_detail.pdf"), bbox_inches="tight")
fig.savefig(os.path.join(figs, "fig2b_phase3_pair_detail.png"), bbox_inches="tight")
plt.close(fig)
print("figures written to", figs)
