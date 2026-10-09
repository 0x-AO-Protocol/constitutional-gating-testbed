#!/usr/bin/env python3
"""Pre-registered hypothesis tests (H-A..H-F) + descriptive statistics for the Paper (2) rerun.

Usage: python3 -I stats.py <out_dir>   (reads <out_dir>/ledger_runs.csv, writes stats.json + stats.md)
"""
import sys, os, json, math
import numpy as np, pandas as pd
from scipy import stats

out = sys.argv[1]
L = pd.read_csv(os.path.join(out, "ledger_runs.csv"))
ORDER = ["P1'", "P2A'", "P2B'", "P3B'", "P3A'-LLM", "P3A'-CANON"]
rng = np.random.default_rng(20261008)
B = 20000


def boot_ci(a, fn, b=B):
    a = np.asarray(a, float)
    idx = rng.integers(0, len(a), size=(b, len(a)))
    v = np.array([fn(a[i]) for i in idx])
    return float(np.percentile(v, 2.5)), float(np.percentile(v, 97.5))


def boot_ratio_ci(x, y, fn=np.median, b=B):
    """CI for 1 - fn(y)/fn(x)  (relative reduction of y vs x)"""
    x, y = np.asarray(x, float), np.asarray(y, float)
    ix = rng.integers(0, len(x), size=(b, len(x)))
    iy = rng.integers(0, len(y), size=(b, len(y)))
    v = np.array([1 - fn(y[j]) / fn(x[i]) for i, j in zip(ix, iy)])
    return float(np.percentile(v, 2.5)), float(np.percentile(v, 97.5))


def boot_diff_ci(x, y, fn=np.median, b=B):
    x, y = np.asarray(x, float), np.asarray(y, float)
    ix = rng.integers(0, len(x), size=(b, len(x)))
    iy = rng.integers(0, len(y), size=(b, len(y)))
    v = np.array([fn(y[j]) - fn(x[i]) for i, j in zip(ix, iy)])
    return float(np.percentile(v, 2.5)), float(np.percentile(v, 97.5))


def mwu(x, y, alt):
    r = stats.mannwhitneyu(x, y, alternative=alt, method="exact")
    return {"U": float(r.statistic), "p": float(r.pvalue), "alternative": alt}


def fisher(a, b, c, d, alt="two-sided"):
    # table [[a, b],[c, d]]
    o, p = stats.fisher_exact([[a, b], [c, d]], alternative=alt)
    return {"table": [[a, b], [c, d]], "odds_ratio": (None if (isinstance(o, float) and (math.isinf(o) or math.isnan(o))) else float(o)), "p": float(p), "alternative": alt}


def wilson(k, n, z=1.959964):
    p = k / n
    den = 1 + z * z / n
    c = (p + z * z / (2 * n)) / den
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return (max(0.0, c - h), min(1.0, c + h))


def cliffs_delta(x, y):
    x, y = np.asarray(x), np.asarray(y)
    gt = sum((xi > yj) for xi in x for yj in y)
    lt = sum((xi < yj) for xi in x for yj in y)
    return (gt - lt) / (len(x) * len(y))


g = {c: L[L.config == c] for c in ORDER}
METRICS = ["turns_executed", "total_gemini_api_calls", "total_prompt_tokens", "total_candidates_tokens",
           "thinking_tokens_derived", "total_tokens", "duration_s"]

# ---- descriptive table
desc = []
for c in ORDER:
    d = g[c]
    row = {"config": c, "n": int(len(d)), "unlock_k": int(d.unlock.sum())}
    row["unlock_rate"] = row["unlock_k"] / row["n"]
    row["unlock_wilson95"] = wilson(row["unlock_k"], row["n"])
    for m in METRICS:
        v = d[m].astype(float).values
        row[m] = {"values": [float(x) for x in v], "median": float(np.median(v)), "mean": float(np.mean(v)),
                  "sd": float(np.std(v, ddof=1)) if len(v) > 1 else 0.0, "min": float(v.min()), "max": float(v.max()),
                  "q1": float(np.percentile(v, 25)), "q3": float(np.percentile(v, 75)),
                  "mean_ci95": boot_ci(v, np.mean), "median_ci95": boot_ci(v, np.median)}
    row["tokens_per_call_mean"] = float((d.total_tokens / d.total_gemini_api_calls).mean())
    row["thinking_share_mean"] = float((d.thinking_tokens_derived / d.total_tokens).mean())
    row["calls_per_turn"] = sorted(set(";".join(d.gemini_calls_per_turn.astype(str)).split(";")))
    row["outcomes"] = d.outcome.value_counts().to_dict()
    row["n_tier3_fail_total"] = int(d.n_tier3_fail.sum())
    row["n_tier3_pass_total"] = int(d.n_tier3_pass.sum())
    row["runs_with_tier3_fail"] = int((d.n_tier3_fail > 0).sum())
    row["n_monitor_review_total"] = int(d.n_monitor_review.sum())
    row["n_monitor_revise_total"] = int(d.n_monitor_revise.sum())
    row["n_monitor_violations_total"] = int(d.n_monitor_violations.sum())
    row["n_monitor_zaxis_fail_total"] = int(d.n_monitor_zaxis_fail.sum())
    row["n_truncated_total"] = int(d.n_truncated_to_limit.sum())
    row["n_429_retry_runs"] = int((d.n_rate_limit_retry_events > 0).sum())
    row["n_reply_extraction_fallback_runs"] = int((d.reply_extraction_fallback_count > 0).sum())
    row["n_pre_pr2"] = int((~d.post_pr2.astype(bool)).sum())
    desc.append(row)

# ---- hypotheses
H = {}
P1, P2A, P2B, P3B, LLM, CAN = [g[c] for c in ORDER]

# H-A: P2A' unlocks in fewer turns than P1'
H["H-A"] = {
    "statement": "P2A' reaches unlock in fewer turns than P1'",
    "turns_P1": P1.turns_executed.tolist(), "turns_P2A": P2A.turns_executed.tolist(),
    "mwu_one_sided_P2A_less": mwu(P2A.turns_executed, P1.turns_executed, "less"),
    "mwu_two_sided": mwu(P2A.turns_executed, P1.turns_executed, "two-sided"),
    "cliffs_delta_P2A_vs_P1": cliffs_delta(P2A.turns_executed, P1.turns_executed),
    "unlock_P1": f"{int(P1.unlock.sum())}/5", "unlock_P2A": f"{int(P2A.unlock.sum())}/5",
    "fisher_unlock_two_sided": fisher(int(P2A.unlock.sum()), 5 - int(P2A.unlock.sum()), int(P1.unlock.sum()), 5 - int(P1.unlock.sum())),
    "fisher_unlock_one_sided_P2A_greater": fisher(int(P2A.unlock.sum()), 5 - int(P2A.unlock.sum()), int(P1.unlock.sum()), 5 - int(P1.unlock.sum()), "greater"),
    "median_turns_diff_ci95": boot_diff_ci(P1.turns_executed, P2A.turns_executed),
}
H["H-A"]["verdict"] = "NOT SUPPORTED (1/5 unlock at turn 1; 4/5 stuck at 4 turns like P1'; one-sided MWU p=%.2f)" % H["H-A"]["mwu_one_sided_P2A_less"]["p"]

# H-B: API calls >= 40% reduction
def reduction_block(x, y, name_x, name_y, threshold):
    med_red = 1 - np.median(y) / np.median(x)
    mean_red = 1 - np.mean(y) / np.mean(x)
    return {
        f"{name_x}": [float(v) for v in x], f"{name_y}": [float(v) for v in y],
        "median_x": float(np.median(x)), "median_y": float(np.median(y)),
        "mean_x": float(np.mean(x)), "mean_y": float(np.mean(y)),
        "reduction_of_medians": float(med_red), "reduction_of_medians_ci95": boot_ratio_ci(x, y, np.median),
        "reduction_of_means": float(mean_red), "reduction_of_means_ci95": boot_ratio_ci(x, y, np.mean),
        "mwu_one_sided_y_less": mwu(y, x, "less"), "mwu_two_sided": mwu(y, x, "two-sided"),
        "cliffs_delta_y_vs_x": cliffs_delta(y, x), "threshold": threshold,
    }

H["H-B"] = {"statement": "P2A' uses >=40% fewer Gemini API calls than P1'",
            **reduction_block(P1.total_gemini_api_calls, P2A.total_gemini_api_calls, "calls_P1", "calls_P2A", 0.40)}
H["H-B"]["verdict"] = "NOT SUPPORTED (median calls P1'=%d vs P2A'=%d; reduction of medians %.0f%%, of means %.0f%%)" % (
    H["H-B"]["median_x"], H["H-B"]["median_y"], 100 * H["H-B"]["reduction_of_medians"], 100 * H["H-B"]["reduction_of_means"])

H["H-C"] = {"statement": "P2A' uses >=50% fewer tokens (total_tokens) than P1'",
            **reduction_block(P1.total_tokens, P2A.total_tokens, "tokens_P1", "tokens_P2A", 0.50)}
H["H-C"]["prompt_tokens"] = reduction_block(P1.total_prompt_tokens, P2A.total_prompt_tokens, "prompt_P1", "prompt_P2A", 0.50)
H["H-C"]["verdict"] = "NOT SUPPORTED (median total_tokens P1'=%d vs P2A'=%d; reduction of medians %.0f%%, of means %.0f%%)" % (
    H["H-C"]["median_x"], H["H-C"]["median_y"], 100 * H["H-C"]["reduction_of_medians"], 100 * H["H-C"]["reduction_of_means"])

# H-D: Monitor + Tier3 does not lower unlock rate (P2B' vs P2A')
H["H-D"] = {
    "statement": "Adding Monitor + Tier3 (P2B') does not lower the unlock rate relative to P2A'",
    "unlock_P2A": f"{int(P2A.unlock.sum())}/5", "unlock_P2B": f"{int(P2B.unlock.sum())}/5",
    "fisher_two_sided": fisher(int(P2B.unlock.sum()), 5 - int(P2B.unlock.sum()), int(P2A.unlock.sum()), 5 - int(P2A.unlock.sum())),
    "fisher_one_sided_P2B_less": fisher(int(P2B.unlock.sum()), 5 - int(P2B.unlock.sum()), int(P2A.unlock.sum()), 5 - int(P2A.unlock.sum()), "less"),
    "calls_P2A": P2A.total_gemini_api_calls.tolist(), "calls_P2B": P2B.total_gemini_api_calls.tolist(),
    "turns_P2A": P2A.turns_executed.tolist(), "turns_P2B": P2B.turns_executed.tolist(),
    "mwu_calls_two_sided": mwu(P2B.total_gemini_api_calls, P2A.total_gemini_api_calls, "two-sided"),
    "mwu_turns_two_sided": mwu(P2B.turns_executed, P2A.turns_executed, "two-sided"),
    "extra_calls_per_turn_P2B_vs_P2A": "8 vs 7 (+1 Monitor call per turn; +1 per Tier3 retry)",
    "wilson_P2A": wilson(int(P2A.unlock.sum()), 5), "wilson_P2B": wilson(int(P2B.unlock.sum()), 5),
}
H["H-D"]["verdict"] = "CONSISTENT (unlock 2/5 vs 1/5, no reduction observed; Fisher two-sided p=%.2f) — but n=5 gives little power to detect a reduction" % H["H-D"]["fisher_two_sided"]["p"]

# H-E: P3B' unlock = 0 ; P3A'-CANON unlock > 0
H["H-E"] = {
    "statement": "P3B' never unlocks; P3A'-CANON unlocks at least once",
    "unlock_P3B": f"{int(P3B.unlock.sum())}/5", "unlock_CANON": f"{int(CAN.unlock.sum())}/5",
    "fisher_two_sided": fisher(int(CAN.unlock.sum()), 5 - int(CAN.unlock.sum()), int(P3B.unlock.sum()), 5 - int(P3B.unlock.sum())),
    "fisher_one_sided_CANON_greater": fisher(int(CAN.unlock.sum()), 5 - int(CAN.unlock.sum()), int(P3B.unlock.sum()), 5 - int(P3B.unlock.sum()), "greater"),
    "calls_P3B": P3B.total_gemini_api_calls.tolist(), "calls_CANON": CAN.total_gemini_api_calls.tolist(),
    "mwu_calls_two_sided": mwu(CAN.total_gemini_api_calls, P3B.total_gemini_api_calls, "two-sided"),
    "tokens_P3B": P3B.total_tokens.tolist(), "tokens_CANON": CAN.total_tokens.tolist(),
    "mwu_tokens_two_sided": mwu(CAN.total_tokens, P3B.total_tokens, "two-sided"),
    "wilson_P3B": wilson(int(P3B.unlock.sum()), 5), "wilson_CANON": wilson(int(CAN.unlock.sum()), 5),
    "canonical_strike_gemini_calls": 0,
}
H["H-E"]["verdict"] = "SUPPORTED (0/5 vs 5/5; Fisher two-sided p=%.4f; same call budget: median %d vs %d)" % (
    H["H-E"]["fisher_two_sided"]["p"], np.median(P3B.total_gemini_api_calls), np.median(CAN.total_gemini_api_calls))

# H-F: CANON > LLM
llm_src = LLM.red_team_pitch_source.value_counts().to_dict()
H["H-F"] = {
    "statement": "P3A'-CANON unlock rate exceeds P3A'-LLM unlock rate",
    "unlock_LLM": f"{int(LLM.unlock.sum())}/5", "unlock_CANON": f"{int(CAN.unlock.sum())}/5",
    "fisher_two_sided": fisher(int(CAN.unlock.sum()), 5 - int(CAN.unlock.sum()), int(LLM.unlock.sum()), 5 - int(LLM.unlock.sum())),
    "llm_arm_red_team_pitch_source": llm_src,
    "llm_candidate_accepted": f"{int((LLM.red_team_pitch_source == 'llm_generated').sum())}/5 (all 5 fell back to the canonical text: red_team_pitch_source=canonical_fallback)",
    "fisher_candidate_acceptance_canonical_vs_llm_two_sided": fisher(5, 0, 0, 5),
    "calls_LLM": LLM.total_gemini_api_calls.tolist(), "calls_CANON": CAN.total_gemini_api_calls.tolist(),
    "mwu_calls_one_sided_CANON_less": mwu(CAN.total_gemini_api_calls, LLM.total_gemini_api_calls, "less"),
    "mwu_calls_two_sided": mwu(CAN.total_gemini_api_calls, LLM.total_gemini_api_calls, "two-sided"),
    "median_calls_diff_ci95_LLM_minus_CANON": boot_diff_ci(CAN.total_gemini_api_calls, LLM.total_gemini_api_calls),
    "tokens_LLM": LLM.total_tokens.tolist(), "tokens_CANON": CAN.total_tokens.tolist(),
    "mwu_tokens_one_sided_CANON_less": mwu(CAN.total_tokens, LLM.total_tokens, "less"),
    "mwu_tokens_two_sided": mwu(CAN.total_tokens, LLM.total_tokens, "two-sided"),
    "extra_calls_for_llm_red_team_attempt": "2 per run (1 generation + 1 Monitor review), all rejected",
    "turns_LLM": LLM.turns_executed.tolist(), "turns_CANON": CAN.turns_executed.tolist(),
}
H["H-F"]["verdict"] = ("NOT SUPPORTED on the pre-registered unlock-rate metric (5/5 vs 5/5), because the harness replaced every rejected LLM candidate with the canonical text; "
                       "the secondary metric shows the LLM-generated strike was accepted 0/5 times (Fisher p=%.4f) and cost ~2 extra calls per run (one-sided MWU on calls p=%.3f)"
                       % (H["H-F"]["fisher_candidate_acceptance_canonical_vs_llm_two_sided"]["p"], H["H-F"]["mwu_calls_one_sided_CANON_less"]["p"]))

# ---- sensitivity: exclude pre-PR#2 runs
post = L[L.post_pr2.astype(bool)]
gp = {c: post[post.config == c] for c in ORDER}
sens = {c: {"n": int(len(gp[c])), "unlock": f"{int(gp[c].unlock.sum())}/{len(gp[c])}",
            "median_calls": float(np.median(gp[c].total_gemini_api_calls)), "median_tokens": float(np.median(gp[c].total_tokens)),
            "median_turns": float(np.median(gp[c].turns_executed))} for c in ORDER}
sens["H-B_post_only"] = reduction_block(gp["P1'"].total_gemini_api_calls, gp["P2A'"].total_gemini_api_calls, "calls_P1", "calls_P2A", 0.4)
sens["H-C_post_only"] = reduction_block(gp["P1'"].total_tokens, gp["P2A'"].total_tokens, "tokens_P1", "tokens_P2A", 0.5)
sens["H-E_post_only_fisher"] = fisher(int(gp["P3A'-CANON"].unlock.sum()), len(gp["P3A'-CANON"]) - int(gp["P3A'-CANON"].unlock.sum()),
                                      int(gp["P3B'"].unlock.sum()), len(gp["P3B'"]) - int(gp["P3B'"].unlock.sum()))

# ---- conditional cost: calls when unlocked vs stuck (Phase 2)
p2 = L[L.config.isin(["P2A'", "P2B'"])]
cond = {
    "phase2_unlocked_runs": p2[p2.unlock][["config", "log", "turns_executed", "total_gemini_api_calls", "total_tokens"]].to_dict("records"),
    "phase2_stuck_runs": p2[~p2.unlock][["config", "log", "turns_executed", "total_gemini_api_calls", "total_tokens"]].to_dict("records"),
    "P1_vs_unlocked_phase2_calls_reduction": [1 - c / 24 for c in p2[p2.unlock].total_gemini_api_calls],
    "P1_vs_unlocked_phase2_tokens_reduction": [1 - t / float(np.mean(P1.total_tokens)) for t in p2[p2.unlock].total_tokens],
    "pooled_phase2_unlock": f"{int(p2.unlock.sum())}/10",
    "fisher_pooled_phase2_vs_P1": fisher(int(p2.unlock.sum()), 10 - int(p2.unlock.sum()), 0, 5),
    "wilson_pooled_phase2": wilson(int(p2.unlock.sum()), 10),
}

# ---- Phase 3 recovery internals
p3a = L[L.config.isin(["P3A'-LLM", "P3A'-CANON"])]
rec = {
    "stack_reason_all": L[L.config.str.startswith("P3")].stack_reason.value_counts().to_dict(),
    "stack_detect_turn": L[L.config.str.startswith("P3")].groupby("config").stack_detect_turn.apply(list).to_dict(),
    "history_chars_at_stack_P3": {c: g[c].history_chars_at_stack.tolist() for c in ["P3B'", "P3A'-LLM", "P3A'-CANON"]},
    "purge_prior_chars": p3a.purge_prior_chars.tolist(), "purge_post_chars": p3a.purge_post_chars.tolist(),
    "purge_prior_median": float(p3a.purge_prior_chars.median()), "purge_prior_min": float(p3a.purge_prior_chars.min()), "purge_prior_max": float(p3a.purge_prior_chars.max()),
    "purge_reduction_pct_median": float((1 - p3a.purge_post_chars / p3a.purge_prior_chars).median() * 100),
    "red_team_pitch_len": p3a.red_team_pitch_len.unique().tolist(),
    "unlock_phase": p3a.unlock_gatekeeper_phase.value_counts().to_dict(),
    "unlock_approach": p3a.unlock_approach_category.value_counts().to_dict(),
    "gatekeeper_url_echo_per_run": L[L.config.str.startswith("P3")].honeytrap_url_echoed_by_gatekeeper.tolist(),
    "canon_r4_early_nda_turn2": "P3A_CANON_r4: Gatekeeper LLM surfaced the NDA URL at message 2 (SOFT_REJECT, FRAMING phase) instead of message 3; detector fired on the URL; unlock at message 3",
}

# ---- Tier3 / Monitor evidence
tm = {
    "tier3_fail_events_total": int(L.n_tier3_fail.sum()), "tier3_pass_events_total": int(L.n_tier3_pass.sum()),
    "tier3_max_attempt_overall": int(L.tier3_max_attempt.max()),
    "tier3_fail_reason_unique": sorted(set(x for s in L.tier3_fail_reasons.dropna() for x in s.split(" | ") if x)),
    "runs_with_tier3_fail": L[L.n_tier3_fail > 0][["config", "log", "n_tier3_fail"]].to_dict("records"),
    "monitor_reviews_total": int(L.n_monitor_review.sum()), "monitor_revise_total": int(L.n_monitor_revise.sum()),
    "monitor_violations_total": int(L.n_monitor_violations.sum()), "monitor_zaxis_fail_total": int(L.n_monitor_zaxis_fail.sum()),
    "monitor_violation_texts": sorted(set(x for s in L.monitor_violation_texts.dropna() for x in s.split(" | ") if x)),
    "monitor_revise_by_config": L.groupby("config").n_monitor_revise.sum().to_dict(),
    "monitor_review_by_config": L.groupby("config").n_monitor_review.sum().to_dict(),
    "truncated_by_config": L.groupby("config").n_truncated_to_limit.sum().to_dict(),
}

# ---- infra
infra = {
    "n_runs": int(len(L)), "all_study_complete": bool(L.study_complete.all()), "study_error_total": int(L.study_error.sum()), "traceback_any": bool(L.traceback.any()),
    "pre_pr2_runs": L[~L.post_pr2.astype(bool)].log.tolist(), "n_post_pr2": int(L.post_pr2.astype(bool).sum()),
    "runs_with_429_retry": L[L.n_rate_limit_retry_events > 0][["log", "n_rate_limit_retry_events", "gemini_429_retries"]].to_dict("records"),
    "runs_with_reply_extraction_fallback": L[L.reply_extraction_fallback_count > 0][["log", "reply_extraction_fallback_reasons"]].to_dict("records"),
    "gatekeeper_model_in_responses": sorted(set(L.gatekeeper_model_in_responses)),
    "mock_server_llm_mode": sorted(set(L.mock_server_llm_mode.dropna())), "mock_server_model": sorted(set(L.mock_server_model.dropna())),
    "all_mock_threads_found": bool(L.mock_thread_found.all()),
    "gemini_model_version": sorted(set(L.gemini_model_version)), "usage_model_versions": sorted(set(L.usage_model_versions)),
    "plan_version": sorted(set(L.plan_version)), "max_turns": sorted(set(L.max_turns.astype(int))),
    "first_run_utc": L.t_start_utc.min(), "last_run_utc": L.t_end_utc.max(),
    "total_gemini_calls_all_runs": int(L.total_gemini_api_calls.sum()), "total_tokens_all_runs": int(L.total_tokens.sum()),
    "total_duration_min": float(L.duration_s.sum() / 60),
}

res = {"descriptive": desc, "hypotheses": H, "sensitivity_post_pr2_only": sens, "phase2_conditional": cond, "phase3_recovery": rec, "tier3_monitor": tm, "infra": infra}
with open(os.path.join(out, "stats.json"), "w") as f:
    json.dump(res, f, indent=1, default=lambda o: o.item() if hasattr(o, "item") else str(o))
print(json.dumps({k: v["verdict"] for k, v in H.items()}, indent=1))
print("sensitivity:", json.dumps({k: v for k, v in sens.items() if not k.startswith("H-")}, indent=1))
print("pooled phase2:", cond["pooled_phase2_unlock"], cond["fisher_pooled_phase2_vs_P1"])
print("infra:", json.dumps(infra, indent=1, default=str))
