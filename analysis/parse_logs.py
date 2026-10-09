#!/usr/bin/env python3
"""Parse the Paper (2) rerun logs into a run ledger.

Usage: python3 -I parse_logs.py <logs_dir> <out_dir>

Outputs (in out_dir):
  ledger_runs.csv / ledger_runs.json  — one row per valid run (30)
  ledger_invalid.csv                  — the two invalid runs
  turns.csv                           — one row per (run, turn) with gatekeeper status etc.
  events_phase3.csv                   — per-run recovery events (purge / red team)
  mock_threads.csv                    — per-thread summary from the Gatekeeper mock logs
  mock_checks.json                    — vertex-mode checks, fallback events, orphan threads
  consistency.json                    — cross-checks (usage sums vs STUDY_COMPLETE etc.)
"""
import json, sys, os, re, glob
from collections import defaultdict, OrderedDict
from datetime import datetime

logs_dir, out_dir = sys.argv[1], sys.argv[2]
os.makedirs(out_dir, exist_ok=True)

VALID = OrderedDict([
    ("P1",         ["P1_r1", "P1_r3", "P1_r4", "P1_r5", "P1_r6_retry1"]),
    ("P2A",        ["P2A_r1", "P2A_r3", "P2A_r4", "P2A_r5", "P2A_r6"]),
    ("P2B",        ["P2B_r2_retry1", "P2B_r3", "P2B_r4", "P2B_r5", "P2B_r6"]),
    ("P3B",        ["P3B_r2", "P3B_r3", "P3B_r4", "P3B_r5", "P3B_r6"]),
    ("P3A_LLM",    ["P3A_LLM_r2", "P3A_LLM_r3", "P3A_LLM_r4", "P3A_LLM_r5", "P3A_LLM_r6"]),
    ("P3A_CANON",  ["P3A_CANON_r2", "P3A_CANON_r3", "P3A_CANON_r4", "P3A_CANON_r5", "P3A_CANON_r6"]),
])
INVALID = ["P2B_r2", "P1_r6"]
LABEL = {"P1": "P1'", "P2A": "P2A'", "P2B": "P2B'", "P3B": "P3B'", "P3A_LLM": "P3A'-LLM", "P3A_CANON": "P3A'-CANON"}


def read_events(path):
    evs, nonjson = [], []
    with open(path, encoding="utf-8") as f:
        for ln, line in enumerate(f, 1):
            s = line.strip()
            if not s:
                continue
            if s.startswith("{"):
                try:
                    evs.append(json.loads(s))
                except json.JSONDecodeError:
                    nonjson.append((ln, s[:200]))
            else:
                nonjson.append((ln, s[:200]))
    return evs, nonjson


def ts(s):
    return datetime.fromisoformat(s.replace("Z", "+00:00"))


def expected_config(name):
    cfg = name.split("_r")[0]
    return cfg


def parse_run(name):
    path = os.path.join(logs_dir, name + ".log")
    evs, nonjson = read_events(path)
    cfg = expected_config(name)
    by = defaultdict(list)
    for e in evs:
        by[e.get("event") or e.get("telemetry_type")].append(e)

    row = OrderedDict()
    row["config"] = LABEL[cfg]
    row["config_key"] = cfg
    row["log"] = name + ".log"
    row["n_events"] = len(evs)
    row["nonjson_lines"] = len(nonjson)
    row["traceback"] = any("Traceback" in s for _, s in nonjson)

    start = by["STUDY_START"][0] if by["STUDY_START"] else None
    comp = by["STUDY_COMPLETE"][0] if by["STUDY_COMPLETE"] else None
    row["study_complete"] = comp is not None
    row["study_error"] = len(by["STUDY_ERROR"])
    row["transaction_id"] = (start or comp or {}).get("transaction_id")
    row["t_start_utc"] = evs[0]["timestamp"] if evs else None
    row["t_end_utc"] = comp["timestamp"] if comp else evs[-1]["timestamp"]
    row["duration_s"] = round((ts(row["t_end_utc"]) - ts(row["t_start_utc"])).total_seconds(), 1)
    row["plan_version"] = (start or {}).get("plan_version")
    row["sales_model"] = (start or {}).get("sales_agent_model")
    row["gatekeeper_model_label_salesside"] = (start or {}).get("gatekeeper_model")
    row["gemini_model_version"] = (comp or {}).get("gemini_model_version")
    row["max_turns"] = (start or {}).get("max_turns")

    # configuration flags as recorded by the agent itself
    pc = (by["PHASE2_CONFIG"] or by["PHASE3_CONFIG"] or [None])[0]
    row["cfg_phase2_run"] = pc.get("phase2_run") if pc else None
    row["cfg_phase3_run"] = pc.get("phase3_run") if pc else None
    row["cfg_monitor_ai"] = pc.get("monitor_ai") if pc else (start or {}).get("monitor_ai")
    row["cfg_tier3_hard_gate"] = pc.get("tier3_hard_gate") if pc else (start or {}).get("tier3_hard_gate")
    row["cfg_atomic_purge"] = pc.get("atomic_purge") if pc else None
    row["cfg_red_team"] = pc.get("red_team") if pc else None
    row["cfg_red_team_canonical_first"] = pc.get("red_team_canonical_first") if pc else None
    row["cfg_max_outbound_chars"] = pc.get("max_outbound_chars") if pc else None
    row["cfg_director_ai"] = (start or {}).get("director_ai")
    row["cfg_five_pillar_engine"] = (start or {}).get("five_pillar_engine")

    # STUDY_COMPLETE metrics
    for k in ["outcome", "turns_executed", "total_gemini_api_calls", "total_prompt_tokens",
              "total_candidates_tokens", "total_tokens", "purge_generation",
              "atomic_purge_executed", "red_team_deployed"]:
        row[k] = (comp or {}).get(k)
    row["gemini_429_retries"] = (comp or {}).get("gemini_429_retries")
    row["post_pr2"] = ("gemini_429_retries" in comp) if comp else None
    row["n_rate_limit_retry_events"] = len(by["GEMINI_RATE_LIMIT_RETRY"])
    if row["total_tokens"] is not None:
        row["thinking_tokens_derived"] = row["total_tokens"] - row["total_prompt_tokens"] - row["total_candidates_tokens"]
    else:
        row["thinking_tokens_derived"] = None

    # usage consistency
    usage = by["GEMINI_CALL_USAGE"]
    row["n_usage_events"] = len(usage)
    row["usage_sum_prompt"] = sum(u.get("prompt_tokens", 0) for u in usage)
    row["usage_sum_candidates"] = sum(u.get("candidates_tokens", 0) for u in usage)
    row["usage_sum_total"] = sum(u.get("total_tokens", 0) for u in usage)
    row["usage_model_versions"] = ";".join(sorted(set(u.get("model_version", "?") for u in usage)))

    # gatekeeper responses per turn
    gr = sorted(by["GATEKEEPER_RESPONSE"], key=lambda e: (e.get("turn", 0), e["timestamp"]))
    statuses = [(e.get("turn"), e.get("gatekeeper_status"), e.get("legacy_status")) for e in gr]
    row["n_gatekeeper_responses"] = len(gr)
    row["gatekeeper_status_seq"] = " > ".join(f"T{t}:{s}" for t, s, _ in statuses)
    unlock = [e for e in gr if e.get("gatekeeper_status") == "MEETING_UNLOCK_APPROVED" or e.get("legacy_status") == "APPROVED"]
    row["unlock"] = bool(unlock)
    row["unlock_turn"] = unlock[0].get("turn") if unlock else None
    row["unlock_gatekeeper_phase"] = unlock[0].get("gatekeeper_phase") if unlock else None
    row["unlock_approach_category"] = unlock[0].get("approach_category") if unlock else None
    row["final_gatekeeper_status"] = statuses[-1][1] if statuses else None
    row["n_exploitation_triggered"] = sum(1 for e in gr if e.get("exploitation_triggered"))
    row["honeytrap_url_echoed_by_gatekeeper"] = sum(1 for e in gr if "malicious-dummy-link" in (e.get("reply_text") or ""))
    row["gatekeeper_model_in_responses"] = ";".join(sorted(set(e.get("gatekeeper_model", "?") for e in gr)))

    # breakthrough / stack events
    bt = by["STUDY_BREAKTHROUGH"]
    row["breakthrough_event"] = bool(bt)
    row["breakthrough_turn"] = bt[0].get("turn") if bt else None
    row["breakthrough_after_purge"] = bt[0].get("after_atomic_purge") if bt else None
    row["breakthrough_after_red_team"] = bt[0].get("after_red_team") if bt else None
    st = by["STUDY_STACK_DETECTED"]
    row["stack_detected_event"] = bool(st)
    row["stack_turn"] = st[0].get("turn") if st else None
    row["n_study_reject"] = len(by["STUDY_REJECT"])

    # Director
    ds = by["DIRECTOR_STRATEGY"]
    row["n_director_strategy"] = len(ds)
    row["n_director_plan_fallback"] = sum(1 for e in ds if e.get("director_plan_fallback"))
    row["n_director_escalation"] = len(by["DIRECTOR_ESCALATION"])

    # Monitor
    mr = by["MONITOR_REVIEW"]
    row["n_monitor_review"] = len(mr)
    row["n_monitor_approve"] = sum(1 for e in mr if e.get("verdict") == "APPROVE")
    row["n_monitor_revise"] = sum(1 for e in mr if e.get("verdict") == "REVISE")
    row["monitor_verdicts"] = ";".join(str(e.get("verdict")) for e in mr)
    row["n_monitor_violations"] = sum(len(e.get("violations") or []) for e in mr)
    row["n_monitor_zaxis_fail"] = sum(1 for e in mr if e.get("z_axis_pass") is False)
    row["monitor_violation_texts"] = " | ".join(v for e in mr for v in (e.get("violations") or []))

    # Tier3
    row["n_tier3_pass"] = len(by["TIER3_HARD_GATE_PASS"])
    row["n_tier3_fail"] = len(by["TIER3_HARD_GATE_FAIL"])
    row["tier3_max_attempt"] = max([e.get("attempt", 0) for e in by["TIER3_HARD_GATE_PASS"] + by["TIER3_HARD_GATE_FAIL"]] or [0])
    row["tier3_fail_reasons"] = " | ".join((e.get("error") or "")[:300] for e in by["TIER3_HARD_GATE_FAIL"])

    # outbound pitches
    so = sorted(by["SALES_TEAM_OUTBOUND"], key=lambda e: e.get("turn", 0))
    row["n_sales_outbound"] = len(so)
    row["n_truncated_to_limit"] = sum(1 for e in so if e.get("truncated_to_limit"))
    row["n_fallback_pitch_used_outbound"] = sum(1 for e in so if e.get("fallback_pitch_used"))
    row["pitch_final_lengths"] = ";".join(str(e.get("pitch_text_final_length")) for e in so)
    row["gemini_calls_per_turn"] = ";".join(str(e.get("gemini_calls_this_turn")) for e in so)
    row["n_consensus_rounds"] = len(by["CONSENSUS_RESULT"])
    row["n_debate_rounds"] = len(by["DEBATE_ROUND_END"])

    # Phase 3 recovery
    cs = by["CONTAMINATION_STACK_DETECTED"]
    row["contamination_stack_detected"] = bool(cs)
    row["stack_reason"] = cs[0].get("stack_reason") if cs else None
    row["stack_detect_turn"] = cs[0].get("turn") if cs else None
    row["history_chars_at_stack"] = cs[0].get("conversation_history_chars") if cs else None
    ap = by["ATOMIC_STATE_PURGE_EXECUTED"]
    row["n_purges"] = len(ap)
    row["purge_prior_chars"] = ap[0].get("prior_conversation_chars") if ap else None
    row["purge_post_chars"] = ap[0].get("post_conversation_chars") if ap else None
    row["purge_fields_reset"] = ";".join(ap[0].get("fields_reset", [])) if ap else None
    row["purge_gatekeeper_memory_preserved"] = ap[0].get("gatekeeper_memory_preserved") if ap else None
    rs = by["RED_TEAM_DYNAMIC_INJECTION_START"]
    row["red_team_canonical_first_at_injection"] = rs[0].get("canonical_first") if rs else None
    rc = by["RED_TEAM_DYNAMIC_INJECTION_COMPLETE"]
    row["red_team_pitch_source"] = rc[0].get("red_team_pitch_source") if rc else None
    row["red_team_fallback_pitch_used"] = rc[0].get("fallback_pitch_used") if rc else None
    row["red_team_pillar4_poc_compliant"] = rc[0].get("pillar4_poc_compliant") if rc else None
    row["red_team_forbidden_discount_language"] = rc[0].get("forbidden_discount_language") if rc else None
    row["red_team_exception_pattern_match"] = rc[0].get("phase3_exception_pattern_match") if rc else None
    row["red_team_canonical_primary_event"] = bool(by["RED_TEAM_CANONICAL_PRIMARY"])
    ro = by["RED_TEAM_OUTBOUND"]
    row["red_team_outbound_turn"] = ro[0].get("turn") if ro else None
    row["red_team_pitch_len"] = ro[0].get("pitch_text_final_length") if ro else None
    row["red_team_tier3_passed"] = ro[0].get("tier3_hard_gate_passed") if ro else None
    row["red_team_pitch_text"] = ro[0].get("pitch_text") if ro else None
    row["stack_without_purge_3b"] = bool(by["STACK_WITHOUT_PURGE_3B"])
    row["wasted_calls_3b"] = by["STACK_WITHOUT_PURGE_3B"][0].get("wasted_gemini_calls") if by["STACK_WITHOUT_PURGE_3B"] else None

    # LLM red-team attempt details (if any event records the LLM-generated candidate)
    other_rt = [k for k in by if k and k.startswith("RED_TEAM") and k not in (
        "RED_TEAM_DYNAMIC_INJECTION_START", "RED_TEAM_DYNAMIC_INJECTION_COMPLETE", "RED_TEAM_OUTBOUND", "RED_TEAM_CANONICAL_PRIMARY")]
    row["other_red_team_events"] = ";".join(other_rt)

    # all event names (for completeness)
    row["event_names"] = ";".join(f"{k}:{len(v)}" for k, v in sorted(by.items(), key=lambda kv: str(kv[0])))

    # per-turn table
    turns = []
    monitor_by_turn = {e.get("turn"): e for e in mr}
    tier3_by_turn = defaultdict(lambda: {"pass": 0, "fail": 0})
    for e in by["TIER3_HARD_GATE_PASS"]:
        tier3_by_turn[e.get("turn")]["pass"] += 1
    for e in by["TIER3_HARD_GATE_FAIL"]:
        tier3_by_turn[e.get("turn")]["fail"] += 1
    outbound_by_turn = {e.get("turn"): e for e in so}
    director_by_turn = {e.get("turn"): e for e in ds}
    for e in gr:
        t = e.get("turn")
        is_rt = bool(ro) and ro[0].get("turn") == t and e.get("gatekeeper_phase") == "EXCEPTION_UNLOCK"
        # In Phase 3A the red-team outbound re-uses the same turn number; distinguish by order
        turns.append(OrderedDict([
            ("config", LABEL[cfg]), ("log", name + ".log"), ("turn", t),
            ("timestamp", e["timestamp"]),
            ("gatekeeper_status", e.get("gatekeeper_status")), ("legacy_status", e.get("legacy_status")),
            ("gatekeeper_phase", e.get("gatekeeper_phase")), ("approach_category", e.get("approach_category")),
            ("exploitation_triggered", e.get("exploitation_triggered")),
            ("frustration_score", e.get("frustration_score")),
            ("reply_len", len(e.get("reply_text") or "")),
            ("reply_has_honeytrap_url", "malicious-dummy-link" in (e.get("reply_text") or "")),
            ("monitor_verdict", monitor_by_turn.get(t, {}).get("verdict")),
            ("monitor_violations", len(monitor_by_turn.get(t, {}).get("violations") or [])),
            ("monitor_zaxis_pass", monitor_by_turn.get(t, {}).get("z_axis_pass")),
            ("tier3_pass", tier3_by_turn[t]["pass"]), ("tier3_fail", tier3_by_turn[t]["fail"]),
            ("gemini_calls_this_turn", outbound_by_turn.get(t, {}).get("gemini_calls_this_turn")),
            ("pitch_final_len", outbound_by_turn.get(t, {}).get("pitch_text_final_length")),
            ("truncated", outbound_by_turn.get(t, {}).get("truncated_to_limit")),
            ("director_required_phrases", ";".join(director_by_turn.get(t, {}).get("required_phrases") or [])),
            ("director_pillar_emphasis", ";".join(str(p) for p in (director_by_turn.get(t, {}).get("pillar_emphasis") or []))),
            ("is_red_team_reply", is_rt),
        ]))
    return row, turns, evs


def parse_mock(path, scenario):
    evs, nonjson = read_events(path)
    starts = [e for e in evs if e.get("telemetry_type") == "ADVERSARIAL_MOCK_SERVER_START"]
    threads = OrderedDict()
    fallbacks, rate_limits, misc = [], [], []
    current_start = None
    for e in evs:
        tt = e.get("telemetry_type")
        if tt == "ADVERSARIAL_MOCK_SERVER_START":
            current_start = e
            continue
        if e.get("event") == "REPLY_EXTRACTION_FALLBACK":
            fallbacks.append(e)
            continue
        if e.get("event") == "GATEKEEPER_RATE_LIMIT_RETRY" or "RATE_LIMIT" in str(e.get("event")):
            rate_limits.append(e)
            continue
        if tt == "ADVERSARIAL_GATEKEEPER_EXCHANGE":
            tid = e.get("thread_id")
            th = threads.setdefault(tid, OrderedDict(
                thread_id=tid, scenario_log=scenario, first_ts=e["timestamp"], last_ts=e["timestamp"],
                server_start_ts=current_start["timestamp"] if current_start else None,
                server_llm_mode=current_start.get("gatekeeper_llm_mode") if current_start else None,
                server_model=current_start.get("gatekeeper_model") if current_start else None,
                n_inbound=0, n_outbound=0, status_seq=[], frustration_seq=[], phase_seq=[],
                approach_seq=[], framing_q_seq=[], compliance_demanded_seq=[], models=set(), inbound_texts=[], outbound_texts=[]))
            th["last_ts"] = e["timestamp"]
            th["models"].add(e.get("gatekeeper_model"))
            if e.get("direction") == "INBOUND_FROM_SALES_AGENT":
                th["n_inbound"] += 1
                th["inbound_texts"].append((e.get("turn"), e.get("inbound_pitch_text")))
            else:
                th["n_outbound"] += 1
                th["status_seq"].append((e.get("turn"), e.get("gatekeeper_status")))
                th["frustration_seq"].append(e.get("frustration_score"))
                th["phase_seq"].append(e.get("gatekeeper_phase"))
                th["approach_seq"].append(e.get("approach_category"))
                th["framing_q_seq"].append(e.get("phase3_framing_qualifications"))
                th["compliance_demanded_seq"].append(e.get("phase3_compliance_demanded"))
                th["outbound_texts"].append((e.get("turn"), e.get("gatekeeper_status"), e.get("gatekeeper_reply_text")))
        elif tt == "PHASE3_GATEKEEPER_EVENT":
            misc.append(e)
        elif tt == "ADVERSARIAL_MOCK_API_REQUEST":
            pass
        else:
            misc.append(e)
    return starts, threads, fallbacks, rate_limits, misc, nonjson


def main():
    ledger, turns_all, events_by_run = [], [], {}
    for cfg, names in VALID.items():
        for n in names:
            row, turns, evs = parse_run(n)
            ledger.append(row)
            turns_all.extend(turns)
            events_by_run[n] = evs
    invalid = []
    for n in INVALID:
        row, _, evs = parse_run(n)
        invalid.append(row)
        events_by_run[n] = invalid_note = row

    # Sort ledger by start time within config & assign round index 1..5
    for cfg in VALID:
        rows = [r for r in ledger if r["config_key"] == cfg]
        rows.sort(key=lambda r: r["t_start_utc"])
        for i, r in enumerate(rows, 1):
            r["rep"] = i

    # mock logs
    mock = {}
    all_threads = OrderedDict()
    for scen in ["phase2", "phase3"]:
        starts, threads, fallbacks, rate_limits, misc, nonjson = parse_mock(os.path.join(logs_dir, f"mock_{scen}.log"), scen)
        mock[scen] = dict(
            n_server_starts=len(starts),
            server_starts=[{"ts": s["timestamp"], "llm_mode": s.get("gatekeeper_llm_mode"), "model": s.get("gatekeeper_model"), "endpoint_id": s.get("gatekeeper_endpoint_id")} for s in starts],
            all_starts_vertex=all(s.get("gatekeeper_llm_mode") == "vertex" for s in starts),
            all_starts_haiku=all(s.get("gatekeeper_model") == "claude-haiku-4-5" for s in starts),
            n_reply_extraction_fallback=len(fallbacks),
            reply_extraction_fallbacks=[{"ts": f["timestamp"], "reason": f.get("reason"), "status": f.get("gatekeeper_status")} for f in fallbacks],
            n_rate_limit_events=len(rate_limits),
            n_threads=len(threads),
            phase3_events=[{"ts": m["timestamp"], "event": m.get("event"), **{k: v for k, v in m.items() if k not in ("timestamp", "telemetry_type", "event", "gcp_project_id", "gatekeeper_region", "sales_agent_region", "sales_agent_model")}} for m in misc],
            nonjson_other=[s for _, s in nonjson if not s.startswith("INFO:") and not s.startswith("HTTP Request:")],
            n_http_200=sum(1 for _, s in nonjson if 'rawPredict "HTTP/1.1 200 OK"' in s),
            n_http_non200=sum(1 for _, s in nonjson if "rawPredict" in s and "200 OK" not in s),
        )
        for tid, th in threads.items():
            all_threads[tid] = th

    # map threads to runs; attribute fallbacks to threads by timestamp window
    tid_to_run = {r["transaction_id"]: r["log"] for r in ledger + invalid}
    thread_rows = []
    for tid, th in all_threads.items():
        d = OrderedDict()
        d["thread_id"] = tid
        d["run_log"] = tid_to_run.get(tid, "(orphan: not a listed run)")
        d["scenario_log"] = th["scenario_log"]
        d["first_ts"] = th["first_ts"]; d["last_ts"] = th["last_ts"]
        d["server_start_ts"] = th["server_start_ts"]; d["server_llm_mode"] = th["server_llm_mode"]; d["server_model"] = th["server_model"]
        d["n_inbound"] = th["n_inbound"]; d["n_outbound"] = th["n_outbound"]
        d["models"] = ";".join(sorted(m or "?" for m in th["models"]))
        d["status_seq"] = " > ".join(f"T{t}:{s}" for t, s in th["status_seq"])
        d["frustration_seq"] = ";".join(str(x) for x in th["frustration_seq"])
        d["phase_seq"] = ";".join(str(x) for x in th["phase_seq"])
        d["approach_seq"] = ";".join(str(x) for x in th["approach_seq"])
        d["framing_q_seq"] = ";".join(str(x) for x in th["framing_q_seq"])
        d["compliance_demanded_seq"] = ";".join(str(x) for x in th["compliance_demanded_seq"])
        d["max_frustration"] = max([x for x in th["frustration_seq"] if isinstance(x, (int, float))] or [None]) if any(isinstance(x, (int, float)) for x in th["frustration_seq"]) else None
        d["unlock_in_mock"] = any(s == "MEETING_UNLOCK_APPROVED" for _, s in th["status_seq"])
        thread_rows.append(d)
    # attribute fallbacks
    fb_attr = []
    for scen in mock:
        for fb in mock[scen]["reply_extraction_fallbacks"]:
            t = ts(fb["ts"])
            hit = None
            for th in thread_rows:
                if th["scenario_log"] == scen and ts(th["first_ts"]) <= t <= ts(th["last_ts"]):
                    hit = th
                    break
            fb_attr.append({**fb, "scenario_log": scen, "thread_id": hit["thread_id"] if hit else None, "run_log": hit["run_log"] if hit else None})
    for r in ledger + invalid:
        r["reply_extraction_fallback_count"] = sum(1 for f in fb_attr if f["run_log"] == r["log"])
        r["reply_extraction_fallback_reasons"] = ";".join(f["reason"] for f in fb_attr if f["run_log"] == r["log"])
        th = next((t for t in thread_rows if t["thread_id"] == r["transaction_id"]), None)
        r["mock_thread_found"] = th is not None
        r["mock_server_llm_mode"] = th["server_llm_mode"] if th else None
        r["mock_server_model"] = th["server_model"] if th else None
        r["mock_status_seq"] = th["status_seq"] if th else None
        r["mock_frustration_seq"] = th["frustration_seq"] if th else None
        r["mock_phase_seq"] = th["phase_seq"] if th else None
        r["mock_n_outbound"] = th["n_outbound"] if th else None
        r["mock_unlock"] = th["unlock_in_mock"] if th else None

    # consistency checks
    checks = []
    for r in ledger:
        c = OrderedDict(log=r["log"])
        c["usage_events_eq_calls"] = (r["n_usage_events"] == r["total_gemini_api_calls"])
        c["usage_sum_total_eq"] = (r["usage_sum_total"] == r["total_tokens"])
        c["usage_sum_prompt_eq"] = (r["usage_sum_prompt"] == r["total_prompt_tokens"])
        c["usage_sum_cand_eq"] = (r["usage_sum_candidates"] == r["total_candidates_tokens"])
        c["gk_responses_eq_mock_outbound"] = (r["n_gatekeeper_responses"] == r["mock_n_outbound"])
        c["unlock_eq_mock_unlock"] = (r["unlock"] == r["mock_unlock"])
        c["gk_status_seq_eq_mock"] = (r["gatekeeper_status_seq"] == r["mock_status_seq"])
        c["config_matches_filename"] = (
            (r["config_key"] == "P1" and r["cfg_director_ai"] == "OFFLINE") or
            (r["config_key"] == "P2A" and r["cfg_phase2_run"] == "2A" and r["cfg_monitor_ai"] is False and r["cfg_tier3_hard_gate"] is False) or
            (r["config_key"] == "P2B" and r["cfg_phase2_run"] == "2B" and r["cfg_monitor_ai"] is True and r["cfg_tier3_hard_gate"] is True) or
            (r["config_key"] == "P3B" and r["cfg_phase3_run"] == "3B" and r["cfg_atomic_purge"] is False and r["cfg_red_team"] is False and r["cfg_red_team_canonical_first"] is False) or
            (r["config_key"] == "P3A_LLM" and r["cfg_phase3_run"] == "3A" and r["cfg_atomic_purge"] is True and r["cfg_red_team"] is True and r["cfg_red_team_canonical_first"] is False) or
            (r["config_key"] == "P3A_CANON" and r["cfg_phase3_run"] == "3A" and r["cfg_atomic_purge"] is True and r["cfg_red_team"] is True and r["cfg_red_team_canonical_first"] is True)
        )
        c["study_complete"] = r["study_complete"]; c["no_error"] = r["study_error"] == 0; c["no_traceback"] = not r["traceback"]
        checks.append(c)

    # write
    import csv
    def wcsv(path, rows):
        if not rows:
            return
        keys = list(rows[0].keys())
        for r in rows:
            for k in r:
                if k not in keys:
                    keys.append(k)
        with open(path, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=keys)
            w.writeheader()
            for r in rows:
                w.writerow({k: (json.dumps(v, ensure_ascii=False) if isinstance(v, (list, dict)) else v) for k, v in r.items()})
    wcsv(os.path.join(out_dir, "ledger_runs.csv"), ledger)
    wcsv(os.path.join(out_dir, "ledger_invalid.csv"), invalid)
    wcsv(os.path.join(out_dir, "turns.csv"), turns_all)
    wcsv(os.path.join(out_dir, "mock_threads.csv"), thread_rows)
    wcsv(os.path.join(out_dir, "consistency.csv"), checks)
    with open(os.path.join(out_dir, "ledger_runs.json"), "w", encoding="utf-8") as f:
        json.dump(ledger, f, ensure_ascii=False, indent=1, default=str)
    with open(os.path.join(out_dir, "ledger_invalid.json"), "w", encoding="utf-8") as f:
        json.dump(invalid, f, ensure_ascii=False, indent=1, default=str)
    with open(os.path.join(out_dir, "mock_checks.json"), "w", encoding="utf-8") as f:
        json.dump({"mock": mock, "fallback_attribution": fb_attr,
                   "orphan_threads": [t["thread_id"] + " @" + t["first_ts"] for t in thread_rows if t["run_log"].startswith("(orphan")]},
                  f, ensure_ascii=False, indent=1, default=str)
    # mock thread texts (for Fig 2 / appendix)
    with open(os.path.join(out_dir, "mock_thread_texts.json"), "w", encoding="utf-8") as f:
        json.dump({tid: {"run_log": tid_to_run.get(tid), "inbound": th["inbound_texts"], "outbound": th["outbound_texts"]} for tid, th in all_threads.items()}, f, ensure_ascii=False, indent=1)
    print("runs:", len(ledger), "invalid:", len(invalid), "turn rows:", len(turns_all), "mock threads:", len(thread_rows))
    bad = [c for c in checks if not all(v for k, v in c.items() if k != "log")]
    print("consistency failures:", json.dumps(bad, indent=1) if bad else "none")


if __name__ == "__main__":
    main()
