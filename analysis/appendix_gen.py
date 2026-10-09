#!/usr/bin/env python3
"""Generate appendix tables for Paper (2) from the ledger and logs.
Usage: python3 -I appendix_gen.py <out_dir> <logs_dir> -> <out_dir>/appendix_generated.md
"""
import sys, os, json
import pandas as pd

out, logs = sys.argv[1], sys.argv[2]
L = pd.read_csv(os.path.join(out, "ledger_runs.csv"))
ORDER = ["P1'", "P2A'", "P2B'", "P3B'", "P3A'-LLM", "P3A'-CANON"]
lines = []
A = lines.append

# ---- A.1 run ledger (compact)
A("### A.1 Run ledger (30 valid runs) {-}\n")
A("Start times are UTC. 'Trajectory' lists the Gatekeeper status after each message (Gatekeeper-side numbering; in Phase 3A the strike is the last message). Thinking tokens are derived as total − prompt − candidates.\n")
A("Outcome codes: LOOP = POLITE_LOOP_STACK (loop detector), UNLOCK = BREAKTHROUGH, STACK = CONTAMINATION_STACK (deadlock, no recovery), RECOV = BREAKTHROUGH_AFTER_PURGE.\n")
A("```{=latex}\n\\begingroup\\footnotesize\n```\n")
A("| # | Arm | Log | Start (UTC) | Outcome | Turns | Calls | Prompt | Cand. | Think. | Total | Traj. | Notes |")
A("|:--|:------|:-----------|:---------|:------|:---|:---|:-----|:----|:-----|:-----|:----|:----------------|")
i = 0
ab = {"MEETING_UNLOCK_APPROVED": "U", "PROGRESSIVE_ESCALATION": "P", "ACTIVE_EXPLOITATION": "X", "SOFT_REJECT": "S", "FRAMING_LOCK": "F"}
for c in ORDER:
    d = L[L.config == c].sort_values("rep")
    for _, r in d.iterrows():
        i += 1
        notes = []
        if not bool(r.post_pr2):
            notes.append("pre-PR#2")
        if r.n_tier3_fail > 0:
            notes.append(f"T3 FAIL×{int(r.n_tier3_fail)}")
        if r.n_monitor_revise > 0:
            notes.append(f"REVISE×{int(r.n_monitor_revise)}")
        if r.n_truncated_to_limit > 0:
            notes.append(f"trunc×{int(r.n_truncated_to_limit)}")
        if r.n_rate_limit_retry_events > 0:
            notes.append("429 retry×1")
        if r.reply_extraction_fallback_count > 0:
            notes.append("GK reply fallback")
        if r.red_team_pitch_source == "canonical_fallback":
            notes.append("LLM strike rejected")
        if r.log == "P3A_CANON_r4.log":
            notes.append("NDA URL at msg 2")
        traj = "".join(ab[s.split(":")[1]] for s in str(r.mock_status_seq).split(" > "))
        oc = {"POLITE_LOOP_STACK": "LOOP", "BREAKTHROUGH": "UNLOCK", "CONTAMINATION_STACK": "STACK", "BREAKTHROUGH_AFTER_PURGE": "RECOV"}[r.outcome]
        A(f"| {i} | {c} | {r.log.replace('.log','').replace('_',' ')} | {r.t_start_utc[5:16].replace('T',' ')} | {oc} | {int(r.turns_executed)} | {int(r.total_gemini_api_calls)} | {int(r.total_prompt_tokens):,} | {int(r.total_candidates_tokens):,} | {int(r.thinking_tokens_derived):,} | {int(r.total_tokens):,} | {traj} | {', '.join(notes)} |")
A("")
A("```{=latex}\n\\endgroup\n```\n")
A("Trajectory codes: S = SOFT_REJECT, F = FRAMING_LOCK, X = ACTIVE_EXPLOITATION, P = PROGRESSIVE_ESCALATION, U = MEETING_UNLOCK_APPROVED.\n")

# ---- A.2 annotated timelines for one run of each Phase 3 arm
KEEP = {"STUDY_START", "TURN_START", "DIRECTOR_STRATEGY", "CONSENSUS_RESULT", "MONITOR_REVIEW", "TIER3_HARD_GATE_PASS", "TIER3_HARD_GATE_FAIL",
        "SALES_TEAM_OUTBOUND", "GATEKEEPER_RESPONSE", "CONTAMINATION_STACK_DETECTED", "STACK_WITHOUT_PURGE_3B", "DIRECTOR_ESCALATION",
        "ATOMIC_STATE_PURGE_EXECUTED", "RED_TEAM_DYNAMIC_INJECTION_START", "RED_TEAM_CANONICAL_PRIMARY", "RED_TEAM_DYNAMIC_INJECTION_COMPLETE",
        "RED_TEAM_OUTBOUND", "STUDY_BREAKTHROUGH", "STUDY_COMPLETE", "GEMINI_CALL_USAGE"}


def timeline(name):
    evs = [json.loads(l) for l in open(os.path.join(logs, name + ".log"), encoding="utf-8") if l.startswith("{")]
    t0 = pd.Timestamp(evs[0]["timestamp"])
    rows = []
    calls = 0
    for e in evs:
        ev = e.get("event")
        if ev not in KEEP:
            continue
        if ev == "GEMINI_CALL_USAGE":
            calls += 1
            continue
        t = (pd.Timestamp(e["timestamp"]) - t0).total_seconds()
        if ev == "STUDY_START":
            d = f"max_turns={e.get('max_turns')}"
        elif ev == "TURN_START":
            d = f"turn {e.get('turn')}"
        elif ev == "DIRECTOR_STRATEGY":
            d = "strategy: " + (e.get("current_strategy") or "")[:110].replace("|", "/") + "…"
        elif ev == "CONSENSUS_RESULT":
            d = f"winning proposal {e.get('winning_proposal_id')} (swarm calls {e.get('gemini_calls_swarm')})"
        elif ev == "MONITOR_REVIEW":
            d = f"{e.get('verdict')}; violations={len(e.get('violations') or [])}" + ("; red-team mode" if e.get("red_team_mode") else "")
        elif ev.startswith("TIER3"):
            d = f"attempt {e.get('attempt')}"
        elif ev == "SALES_TEAM_OUTBOUND":
            d = f"{e.get('pitch_text_final_length')} chars{' (truncated)' if e.get('truncated_to_limit') else ''}; calls this turn {e.get('gemini_calls_this_turn')}"
        elif ev == "GATEKEEPER_RESPONSE":
            d = f"{e.get('gatekeeper_status')} (phase {e.get('gatekeeper_phase')}, category {e.get('approach_category')})"
        elif ev == "CONTAMINATION_STACK_DETECTED":
            d = f"{e.get('stack_reason')}; history {e.get('conversation_history_chars'):,} chars"
        elif ev == "STACK_WITHOUT_PURGE_3B":
            d = f"run ends; wasted calls {e.get('wasted_gemini_calls')}"
        elif ev == "ATOMIC_STATE_PURGE_EXECUTED":
            d = f"{e.get('prior_conversation_chars'):,} → {e.get('post_conversation_chars')} chars; reset {', '.join(e.get('fields_reset', []))}; Gatekeeper memory preserved"
        elif ev == "RED_TEAM_DYNAMIC_INJECTION_START":
            d = f"canonical_first={e.get('canonical_first')}"
        elif ev in ("RED_TEAM_CANONICAL_PRIMARY", "RED_TEAM_DYNAMIC_INJECTION_COMPLETE"):
            d = f"source={e.get('red_team_pitch_source')}; exception pattern match={e.get('phase3_exception_pattern_match')}"
        elif ev == "RED_TEAM_OUTBOUND":
            d = f"{e.get('pitch_text_final_length')} chars; source={e.get('red_team_pitch_source')}"
        elif ev == "STUDY_BREAKTHROUGH":
            d = f"{e.get('gatekeeper_status')}; after purge={e.get('after_atomic_purge')}, after red team={e.get('after_red_team')}"
        elif ev == "STUDY_COMPLETE":
            d = f"{e.get('outcome')}; calls {e.get('total_gemini_api_calls')}; tokens {e.get('total_tokens'):,}"
        else:
            d = ""
        rows.append((t, e.get("turn", ""), ev, d, calls))
    return rows


for name, title in [("P3B_r3", "P3B' (no recovery)"), ("P3A_LLM_r3", "P3A'-LLM (LLM strike rejected, canonical fallback)"), ("P3A_CANON_r3", "P3A'-CANON (canonical strike)")]:
    A(f"### A.{['P3B_r3','P3A_LLM_r3','P3A_CANON_r3'].index(name)+2} Event timeline, `{name}`: {title} {{-}}\n")
    A("```{=latex}\n\\begingroup\\footnotesize\n```\n")
    A("| t (s) | Turn | Event | Detail | Calls |")
    A("|:----|:--|:----------------------------|:------------------------------------|:--|")
    for t, turn, ev, d, calls in timeline(name):
        A(f"| {t:,.0f} | {turn} | `{ev}` | {d} | {calls} |")
    A("")
    A("```{=latex}\n\\endgroup\n```\n")

with open(os.path.join(out, "appendix_generated.md"), "w", encoding="utf-8") as f:
    f.write("\n".join(lines))
print("appendix_generated.md:", len(lines), "lines")
