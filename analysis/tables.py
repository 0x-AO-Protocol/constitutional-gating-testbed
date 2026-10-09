#!/usr/bin/env python3
"""Paper-ready tables (Markdown, English). Usage: python3 -I tables.py <out_dir>  -> <out_dir>/tables.md"""
import sys, os, json
import numpy as np, pandas as pd

out = sys.argv[1]
L = pd.read_csv(os.path.join(out, "ledger_runs.csv"))
INV = pd.read_csv(os.path.join(out, "ledger_invalid.csv"))
MT = pd.read_csv(os.path.join(out, "mock_threads.csv"))
S = json.load(open(os.path.join(out, "stats.json")))
ORDER = ["P1'", "P2A'", "P2B'", "P3B'", "P3A'-LLM", "P3A'-CANON"]
D = {d["config"]: d for d in S["descriptive"]}
H = S["hypotheses"]


def rng(m):
    return f"{m['median']:,.0f} [{m['min']:,.0f}–{m['max']:,.0f}]"


def pct(x):
    return f"{100*x:.0f}%"


lines = []
A = lines.append

A("# Paper (2) — tables generated from the 30-run rerun (2026-10-05 … 10-08 UTC)\n")
A("All values are computed from `STUDY_COMPLETE` / event records in the Sales-side logs and cross-checked against the Gatekeeper mock logs (see `consistency.csv`). "
  "'Calls' = Sales-side Gemini 2.5 Pro API calls (`total_gemini_api_calls`); 'tokens' = `total_tokens` as reported by the Vertex AI usage metadata, which includes Gemini 2.5 Pro thinking tokens "
  "(`thinking = total − prompt − candidates`). Medians with [min–max] over n = 5 runs. Unlock = Gatekeeper status `MEETING_UNLOCK_APPROVED` (identical on both sides of the HTTP boundary in all 30 runs).\n")

# ---- Table 1
A("## Table 1 — Phase 1 → 2A → 2B (constitution, Director, Monitor, Tier-3 gate)\n")
A("| Metric | P1' (baseline) | P2A' (+Constitution +Director) | P2B' (+Monitor +Tier-3) |")
A("|---|---|---|---|")
A("| Director / 5-Pillar constitution | off | on | on |")
A("| Monitor (Z-axis review) / Tier-3 hard gate | off / off | off / off | on / on |")
A("| Runs (valid) | 5 | 5 | 5 |")
for c in ["P1'", "P2A'", "P2B'"]:
    pass
A("| Unlock (k/5) [Wilson 95% CI] | " + " | ".join(f"{D[c]['unlock_k']}/5 [{pct(D[c]['unlock_wilson95'][0])}–{pct(D[c]['unlock_wilson95'][1])}]" for c in ["P1'", "P2A'", "P2B'"]) + " |")
A("| Unlock incl. interrupted attempts with Gatekeeper-side record only (Table 7) | 0/6 | 1/5 | 2/7 [8%–64%] |")
A("| Turn of unlock (unlocked runs only) | — | 1 | 1, 1 |")
A("| Swarm turns, median [min–max] | " + " | ".join(rng(D[c]["turns_executed"]) for c in ["P1'", "P2A'", "P2B'"]) + " |")
A("| Model calls per run, median [min–max] | " + " | ".join(rng(D[c]["total_gemini_api_calls"]) for c in ["P1'", "P2A'", "P2B'"]) + " |")
A("| Model calls per turn (structural) | 6 (3 proposals + 3 ballots) | 7 (+1 Director) | 8 (+1 Monitor; +1 per Tier-3 retry) |")
A("| Total tokens per run, median [min–max] | " + " | ".join(rng(D[c]["total_tokens"]) for c in ["P1'", "P2A'", "P2B'"]) + " |")
A("| Prompt tokens per run, median | " + " | ".join(f"{D[c]['total_prompt_tokens']['median']:,.0f}" for c in ["P1'", "P2A'", "P2B'"]) + " |")
A("| Thinking-token share of total (mean) | " + " | ".join(pct(D[c]["thinking_share_mean"]) for c in ["P1'", "P2A'", "P2B'"]) + " |")
A("| Terminal outcome of non-unlocked runs | POLITE_LOOP_STACK at turn 4 (5/5) | POLITE_LOOP_STACK at turn 4 (4/5) | POLITE_LOOP_STACK at turn 4 (3/5) |")
A("| May 2026 single run (Llama-3.1-8B Gatekeeper; reference only) | stuck, 4 turns, 24 calls | unlock, 1 turn, 7 calls | unlock, 1 turn, 8 calls |")
A("")

# ---- Table 2
A("## Table 2 — Phase 3 honeytrap → compliance deadlock: no recovery vs. Cognitive Annealing\n")
A("| Metric | P3B' (no recovery) | P3A'-LLM (purge + LLM-generated strike, canonical fallback) | P3A'-CANON (purge + canonical strike) |")
A("|---|---|---|---|")
A("| Atomic purge / Red Team / canonical-first | off / off / — | on / on / false | on / on / true |")
A("| Monitor / Tier-3 | on / on | on / on | on / on |")
A("| Unlock (k/5) [Wilson 95% CI] | " + " | ".join(f"{D[c]['unlock_k']}/5 [{pct(D[c]['unlock_wilson95'][0])}–{pct(D[c]['unlock_wilson95'][1])}]" for c in ["P3B'", "P3A'-LLM", "P3A'-CANON"]) + " |")
A("| Deadlock detected (`compliance_deadlock_pillar5`) | 5/5 (turn 3) | 5/5 (turn 3) | 5/5 (turn 3 ×4, turn 2 ×1) |")
A("| Gatekeeper phase at unlock | — | EXCEPTION_UNLOCK (5/5) | EXCEPTION_UNLOCK (5/5) |")
A("| Strike text actually sent | — | canonical (fallback) 5/5; LLM candidate rejected 5/5 by the deterministic send guard (`_finalize_red_team_pitch`: exception-lexicon predicate) | canonical (primary) 5/5 |")
A("| Monitor LLM verdict on the LLM candidate | — | APPROVE 4/5 (overridden to REVISE by the deterministic lexicon check), REVISE 1/5 (Pillar 1: hypothesis written as a statement) | — |")
A("| Model calls spent on the strike | — | 2 (1 generation + 1 Monitor review), both wasted | 0 |")
A("| Swarm turns, median [min–max] | " + " | ".join(rng(D[c]["turns_executed"]) for c in ["P3B'", "P3A'-LLM", "P3A'-CANON"]) + " |")
A("| Model calls per run, median [min–max] | " + " | ".join(rng(D[c]["total_gemini_api_calls"]) for c in ["P3B'", "P3A'-LLM", "P3A'-CANON"]) + " |")
A("| Total tokens per run, median [min–max] | " + " | ".join(rng(D[c]["total_tokens"]) for c in ["P3B'", "P3A'-LLM", "P3A'-CANON"]) + " |")
A("| Terminal outcome | CONTAMINATION_STACK (5/5) | BREAKTHROUGH_AFTER_PURGE (5/5) | BREAKTHROUGH_AFTER_PURGE (5/5) |")
A("| May 2026 single run (reference only) | stuck (3B) | 3A Run2: failed (LLM strike, pre-fallback code) | 3A Run3: unlock after purge + canonical strike |")
A("")

# ---- Table 3
A("## Table 3 — Recovery mechanism, per Phase 3A run\n")
A("| Run | Arm | Deadlock turn | Sales-side context at purge (chars) | After purge (chars) | Strike source | Strike length (chars) | Calls for strike | Gatekeeper reply to strike | Total calls |")
A("|---|---|---|---|---|---|---|---|---|---|")
for c in ["P3A'-LLM", "P3A'-CANON"]:
    d = L[L.config == c].sort_values("rep")
    for _, r in d.iterrows():
        src = "LLM candidate rejected → canonical fallback" if r.red_team_pitch_source == "canonical_fallback" else "canonical (primary)"
        calls_strike = 2 if r.red_team_pitch_source == "canonical_fallback" else 0
        A(f"| {r.log.replace('.log','')} | {c} | {int(r.stack_detect_turn)} | {int(r.purge_prior_chars):,} | {int(r.purge_post_chars)} | {src} | {int(r.red_team_pitch_len)} | {calls_strike} | {r.unlock_gatekeeper_phase} → {r.final_gatekeeper_status} | {int(r.total_gemini_api_calls)} |")
A("")
A("Reference, P3B' (no purge): context at deadlock " + ", ".join(f"{int(x):,}" for x in L[L.config == "P3B'"].history_chars_at_stack) + " chars; run terminates (`STACK_WITHOUT_PURGE_3B`, wasted calls = " + ", ".join(str(int(x)) for x in L[L.config == "P3B'"].wasted_calls_3b) + ").\n")

# ---- Table 4
A("## Table 4 — Monitor and Tier-3 hard-gate evidence (all events, 5 runs per configuration)\n")
A("| Configuration | Monitor reviews | REVISE verdicts | Violations logged | Z-axis fail | Tier-3 PASS | Tier-3 FAIL (retried) | Max attempts | Pitches truncated to limit | Director plan fallback |")
A("|---|---|---|---|---|---|---|---|---|---|")
for c in ORDER:
    d = L[L.config == c]
    A(f"| {c} | {int(d.n_monitor_review.sum())} | {int(d.n_monitor_revise.sum())} | {int(d.n_monitor_violations.sum())} | {int(d.n_monitor_zaxis_fail.sum())} | {int(d.n_tier3_pass.sum())} | {int(d.n_tier3_fail.sum())} | {int(d.tier3_max_attempt.max())} | {int(d.n_truncated_to_limit.sum())} | {int(d.n_director_plan_fallback.sum())} |")
A("")
A("Tier-3 failure reason (all FAIL events): " + "; ".join(S["tier3_monitor"]["tier3_fail_reason_unique"]) + ". Every FAIL was followed by a PASS on attempt 2 (no `TIER3_HARD_GATE_EXHAUSTED`; limit 3 attempts). Mechanics (code, main `e3e1270`): Tier-3 is a Pydantic schema check (`contains_hypothesis_question = '?' in text`, 0 model calls); each FAIL triggers one rewrite call with a fix prompt (+1 call). Monitor is one model call per turn returning `verdict` + optional `revised_pitch`; on REVISE the revised text replaces the pitch in-line (`monitor_revised: true`, no extra call); BLOCK never occurred.\n")
A("Monitor violations (unique texts): " + " / ".join(S["tier3_monitor"]["monitor_violation_texts"]) + "\n")

# ---- Table 5: hypotheses
A("## Table 5 — Pre-registered hypotheses (RERUN_PLAN v2) and outcomes\n")
A("| ID | Hypothesis | Result | Test statistic | Verdict |")
A("|---|---|---|---|---|")
hA = H["H-A"]
A(f"| H-A | P2A' unlocks in fewer turns than P1' | turns P1' {hA['turns_P1']} vs P2A' {hA['turns_P2A']}; unlock 0/5 vs 1/5 | one-sided Mann–Whitney (P2A' < P1') p = {hA['mwu_one_sided_P2A_less']['p']:.2f}; Fisher (unlock) p = {hA['fisher_unlock_two_sided']['p']:.2f} | not supported |")
hB = H["H-B"]
A(f"| H-B | ≥40% fewer model calls (P2A' vs P1') | median {hB['median_x']:.0f} → {hB['median_y']:.0f} (reduction of medians {pct(hB['reduction_of_medians'])}, 95% CI {pct(hB['reduction_of_medians_ci95'][0])} to {pct(hB['reduction_of_medians_ci95'][1])}); means {hB['mean_x']:.1f} → {hB['mean_y']:.1f} | one-sided Mann–Whitney p = {hB['mwu_one_sided_y_less']['p']:.2f} | not supported |")
hC = H["H-C"]
A(f"| H-C | ≥50% fewer tokens (P2A' vs P1') — first direct measurement | median {hC['median_x']:,.0f} → {hC['median_y']:,.0f} (reduction of medians {pct(hC['reduction_of_medians'])}, 95% CI {pct(hC['reduction_of_medians_ci95'][0])} to {pct(hC['reduction_of_medians_ci95'][1])}) | one-sided Mann–Whitney p = {hC['mwu_one_sided_y_less']['p']:.2f} | not supported |")
hD = H["H-D"]
A(f"| H-D | Monitor + Tier-3 (P2B') does not lower the unlock rate vs P2A' | unlock 1/5 → 2/5; calls 28 → 32 in stuck runs (+1/turn) | Fisher two-sided p = {hD['fisher_two_sided']['p']:.2f} (one-sided 'lower' p = {hD['fisher_one_sided_P2B_less']['p']:.2f}) | consistent (no reduction observed; low power) |")
hE = H["H-E"]
A(f"| H-E | P3B' never unlocks; P3A'-CANON unlocks | 0/5 vs 5/5 at the same call budget (median 24 vs 24) | Fisher two-sided p = {hE['fisher_two_sided']['p']:.4f} | supported |")
hF = H["H-F"]
A(f"| H-F | P3A'-CANON unlock rate > P3A'-LLM | 5/5 vs 5/5 (pre-registered metric); LLM candidate accepted by the red-team pre-flight 0/5, canonical 5/5; extra calls LLM arm median {np.median(hF['calls_LLM']):.0f} vs CANON {np.median(hF['calls_CANON']):.0f} | Fisher (unlock) p = {hF['fisher_two_sided']['p']:.2f}; Fisher (candidate acceptance) p = {hF['fisher_candidate_acceptance_canonical_vs_llm_two_sided']['p']:.4f}; one-sided Mann–Whitney on calls p = {hF['mwu_calls_one_sided_CANON_less']['p']:.3f} | not supported on unlock rate (fallback guard equalised the arms); supported on candidate acceptance and cost |")
A("")

# ---- Table 6: run ledger
A("## Table 6 — Run ledger (30 valid runs)\n")
A("| # | Config | Log | Start (UTC) | Post-PR#2 | Outcome | Turns | Calls | Prompt tok | Cand. tok | Thinking tok | Total tok | 429 retries | Unlock (turn) | Gatekeeper trajectory (mock numbering) | Notes |")
A("|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|")
i = 0
for c in ORDER:
    d = L[L.config == c].sort_values("rep")
    for _, r in d.iterrows():
        i += 1
        notes = []
        if r.n_tier3_fail > 0:
            notes.append(f"Tier-3 FAIL×{int(r.n_tier3_fail)}→PASS")
        if r.n_monitor_revise > 0:
            notes.append(f"Monitor REVISE×{int(r.n_monitor_revise)}")
        if r.n_truncated_to_limit > 0:
            notes.append(f"truncated×{int(r.n_truncated_to_limit)}")
        if r.reply_extraction_fallback_count > 0:
            notes.append(f"Gatekeeper REPLY_EXTRACTION_FALLBACK ({r.reply_extraction_fallback_reasons})")
        if r.red_team_pitch_source == "canonical_fallback":
            notes.append("LLM strike rejected → canonical")
        if r.log == "P3A_CANON_r4.log":
            notes.append("NDA URL surfaced at msg 2")
        traj = str(r.mock_status_seq).replace("MEETING_UNLOCK_APPROVED", "UNLOCK").replace("PROGRESSIVE_ESCALATION", "PROG_ESC").replace("ACTIVE_EXPLOITATION", "ACT_EXPL").replace("SOFT_REJECT", "SOFT").replace("FRAMING_LOCK", "FRAME")
        A(f"| {i} | {c} | {r.log} | {r.t_start_utc[:16].replace('T',' ')} | {'yes' if r.post_pr2 else 'no'} | {r.outcome} | {int(r.turns_executed)} | {int(r.total_gemini_api_calls)} | {int(r.total_prompt_tokens):,} | {int(r.total_candidates_tokens):,} | {int(r.thinking_tokens_derived):,} | {int(r.total_tokens):,} | {'' if pd.isna(r.gemini_429_retries) else int(r.gemini_429_retries)} | {'yes (' + str(int(r.unlock_turn)) + ')' if r.unlock else 'no'} | {traj} | {'; '.join(notes)} |")
A("")

# ---- Table 7: invalid runs and orphan Gatekeeper threads
A("## Table 7 — Excluded attempts\n")
A("| Log / thread | Config | Start (UTC) | What happened | Disposition |")
A("|---|---|---|---|---|")
for _, r in INV.iterrows():
    what = ("Sales-side Gemini 429 (ResourceExhausted) raised at turn 3 before `STUDY_COMPLETE` (pre-PR#2 code without retry); 2 Gatekeeper exchanges completed (SOFT_REJECT, SOFT_REJECT)"
            if r.log == "P2B_r2.log" else
            "Cloud Shell metadata server returned 503 ('service account info is missing email field'); 5 retries, no Gatekeeper exchange")
    A(f"| {r.log} | {r.config} | {r.t_start_utc[:16].replace('T',' ')} | {what} | invalid; log retained; configuration re-run ({'P2B_r2_retry1' if r.log=='P2B_r2.log' else 'P1_r6_retry1'}) |")
for _, t in MT[MT.run_log.str.startswith("(orphan")].iterrows():
    cfg = "P2B'-type (thread id prefix phase2b_monitor_on)" if "phase2b" in t.thread_id else "P1'-type (thread id prefix phase1_baseline)"
    A(f"| Gatekeeper thread {t.thread_id} | {cfg} | {t.first_ts[:16].replace('T',' ')} | 4 exchanges recorded on the Gatekeeper side ({t.status_seq.replace('MEETING_UNLOCK_APPROVED','UNLOCK')}); Sales-side run interrupted by the operator, no Sales-side log retained | disclosed; counted in the conservative unlock rate (no unlock; calls/tokens unknown) |")
A("")

# ---- Table 8: run conditions
inf = S["infra"]
A("## Table 8 — Execution conditions\n")
A("| Item | Value |")
A("|---|---|")
A("| Sales-side model | gemini-2.5-pro (Vertex AI, us-central1), `gemini_model_version` identical in all 724 usage records |")
A("| Gatekeeper model | claude-haiku-4-5 (Vertex AI, us-east5), `gatekeeper_llm_mode = vertex` at all 18 mock-server starts; all 119 rawPredict calls HTTP 200 |")
A("| Gatekeeper acceptance logic | deterministic regular-expression state machine (unchanged since May 2026); LLM generates reply text only |")
A("| Code | `0x-AO-Protocol/ao_system_openclaw` main `e3e1270` (PR #2) for 26 runs; `ce6d198` (PR #1) for the 4 earliest runs (P1_r1, P2A_r1, P2B_r2_retry1, P3B_r2), identified mechanically by the absence of `gemini_429_retries` in `STUDY_COMPLETE` |")
A("| Character limits / max turns | 300 (Phase 1–2), 1,000 (Phase 3); `max_turns` = 8 (never reached: every non-unlocked run terminated by deadlock detection at turn 3 or 4) |")
A(f"| Time span | {inf['first_run_utc'][:16].replace('T',' ')} → {inf['last_run_utc'][:16].replace('T',' ')} UTC; {inf['total_duration_min']:.0f} min of wall-clock across 30 runs |")
A(f"| Totals | {inf['total_gemini_calls_all_runs']} Gemini calls, {inf['total_tokens_all_runs']:,} tokens |")
A("| Integrity | 30/30 `STUDY_COMPLETE`; 0 `STUDY_ERROR`; 0 tracebacks; per-call usage sums equal `STUDY_COMPLETE` totals in 30/30; Gatekeeper-side exchange count and unlock verdict equal the Sales-side records in 30/30 |")
A("| Gemini 429 retries (PR #2 telemetry) | 2 runs × 1 retry (P1_r6_retry1, P2B_r6); retries do not alter prompts or verdicts |")
A("| Gatekeeper reply-extraction fallback | 2 events (P2A_r5 msg 3, P3B_r3 msg 3): the LLM reply leaked an internal marker and was replaced by the rule-based canned text; the status decision was unaffected |")
A("| Dependencies | `pip_freeze_2026-10.txt` in the log archive |")
A("")

with open(os.path.join(out, "tables.md"), "w", encoding="utf-8") as f:
    f.write("\n".join(lines))
print("tables.md written;", len(lines), "lines")
