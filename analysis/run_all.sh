#!/usr/bin/env bash
# Recompute every table, statistic and figure of the paper from the released logs.
# Usage (from the repository root):  bash analysis/run_all.sh
# Requires: pip install -r analysis/requirements-analysis.txt
set -euo pipefail
export SOURCE_DATE_EPOCH=1791417600   # fixed PDF timestamps (2026-10-08 UTC) so reruns are byte-identical
cd "$(dirname "$0")/.."
LOGS=logs/rerun_2026-10
OUT=analysis/out
FIGS=analysis/out/figs
mkdir -p "$OUT" "$FIGS"
python3 -I analysis/parse_logs.py "$LOGS" "$OUT"        # run ledger, per-turn table, Gatekeeper-side checks
python3 -I analysis/stats.py "$OUT"                     # H-A..H-F tests, descriptive statistics -> stats.json
python3 -I analysis/tables.py "$OUT"                    # Tables 3-6 -> tables.md
python3 -I analysis/lexicon_hits.py "$OUT"              # Table 3 lexicon row, Section 5.2 trajectory counts
python3 -I analysis/figures.py "$OUT" "$FIGS"           # Figures 2 and 3
python3 -I analysis/fig3_control_stack.py "$FIGS"       # Figure 1 (diagram; no data)
python3 -I analysis/appendix_gen.py "$OUT" "$LOGS"      # Appendix A event timelines -> appendix_generated.md
echo "done: outputs in $OUT"
