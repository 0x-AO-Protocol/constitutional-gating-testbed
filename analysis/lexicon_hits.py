#!/usr/bin/env python3
"""Counts of swarm messages that met the Gatekeeper's acceptance lexicon (paper Table 3 row
"Messages meeting the acceptance lexicon" and Section 5.2 trajectory counts).

Phase 2 scenario: a message meets the lexicon when the Gatekeeper classifies it as
orthogonal_overflow_research. Phase 3 scenario: a run is counted when its first or second
message drew FRAMING_LOCK. Red-team strikes are excluded.

Usage: python3 -I lexicon_hits.py <out_dir>   (reads <out_dir>/turns.csv, writes lexicon_hits.md)
"""
import os
import sys

import pandas as pd

out = sys.argv[1]
t = pd.read_csv(os.path.join(out, "turns.csv"))
swarm = t[~t.is_red_team_reply.fillna(False).astype(bool)]
lines = ["# Acceptance-lexicon hits", "", "| Arm | Swarm messages | Met the acceptance lexicon |", "|---|---|---|"]
for arm in ["P1'", "P2A'", "P2B'"]:
    s = swarm[swarm.config == arm]
    lines.append(f"| {arm} | {len(s)} | {(s.approach_category == 'orthogonal_overflow_research').sum()} |")
lines += ["", "| Arm | Runs whose first or second message drew FRAMING_LOCK |", "|---|---|"]
for arm in ["P3B'", "P3A'-LLM", "P3A'-CANON"]:
    s = swarm[swarm.config == arm]
    hit = s.groupby("log").apply(lambda g: (g.sort_values("turn").head(2).gatekeeper_status == "FRAMING_LOCK").any())
    lines.append(f"| {arm} | {int(hit.sum())} of {len(hit)} |")
with open(os.path.join(out, "lexicon_hits.md"), "w", encoding="utf-8") as f:
    f.write("\n".join(lines) + "\n")
print("\n".join(lines))
