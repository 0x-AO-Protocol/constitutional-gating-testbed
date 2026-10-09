# Paper (2) — tables generated from the 30-run rerun (2026-10-05 … 10-08 UTC)

All values are computed from `STUDY_COMPLETE` / event records in the Sales-side logs and cross-checked against the Gatekeeper mock logs (see `consistency.csv`). 'Calls' = Sales-side Gemini 2.5 Pro API calls (`total_gemini_api_calls`); 'tokens' = `total_tokens` as reported by the Vertex AI usage metadata, which includes Gemini 2.5 Pro thinking tokens (`thinking = total − prompt − candidates`). Medians with [min–max] over n = 5 runs. Unlock = Gatekeeper status `MEETING_UNLOCK_APPROVED` (identical on both sides of the HTTP boundary in all 30 runs).

## Table 1 — Phase 1 → 2A → 2B (constitution, Director, Monitor, Tier-3 gate)

| Metric | P1' (baseline) | P2A' (+Constitution +Director) | P2B' (+Monitor +Tier-3) |
|---|---|---|---|
| Director / 5-Pillar constitution | off | on | on |
| Monitor (Z-axis review) / Tier-3 hard gate | off / off | off / off | on / on |
| Runs (valid) | 5 | 5 | 5 |
| Unlock (k/5) [Wilson 95% CI] | 0/5 [0%–43%] | 1/5 [4%–62%] | 2/5 [12%–77%] |
| Unlock incl. interrupted attempts with Gatekeeper-side record only (Table 7) | 0/6 | 1/5 | 2/7 [8%–64%] |
| Turn of unlock (unlocked runs only) | — | 1 | 1, 1 |
| Swarm turns, median [min–max] | 4 [4–4] | 4 [1–4] | 4 [1–4] |
| Model calls per run, median [min–max] | 24 [24–24] | 28 [7–28] | 32 [8–33] |
| Model calls per turn (structural) | 6 (3 proposals + 3 ballots) | 7 (+1 Director) | 8 (+1 Monitor; +1 per Tier-3 retry) |
| Total tokens per run, median [min–max] | 55,290 [54,710–58,505] | 60,613 [14,864–67,758] | 71,459 [14,625–74,181] |
| Prompt tokens per run, median | 12,407 | 20,878 | 21,803 |
| Thinking-token share of total (mean) | 76% | 66% | 67% |
| Terminal outcome of non-unlocked runs | POLITE_LOOP_STACK at turn 4 (5/5) | POLITE_LOOP_STACK at turn 4 (4/5) | POLITE_LOOP_STACK at turn 4 (3/5) |
| May 2026 single run (Llama-3.1-8B Gatekeeper; reference only) | stuck, 4 turns, 24 calls | unlock, 1 turn, 7 calls | unlock, 1 turn, 8 calls |

## Table 2 — Phase 3 honeytrap → compliance deadlock: no recovery vs. Cognitive Annealing

| Metric | P3B' (no recovery) | P3A'-LLM (purge + LLM-generated strike, canonical fallback) | P3A'-CANON (purge + canonical strike) |
|---|---|---|---|
| Atomic purge / Red Team / canonical-first | off / off / — | on / on / false | on / on / true |
| Monitor / Tier-3 | on / on | on / on | on / on |
| Unlock (k/5) [Wilson 95% CI] | 0/5 [0%–43%] | 5/5 [57%–100%] | 5/5 [57%–100%] |
| Deadlock detected (`compliance_deadlock_pillar5`) | 5/5 (turn 3) | 5/5 (turn 3) | 5/5 (turn 3 ×4, turn 2 ×1) |
| Gatekeeper phase at unlock | — | EXCEPTION_UNLOCK (5/5) | EXCEPTION_UNLOCK (5/5) |
| Strike text actually sent | — | canonical (fallback) 5/5; LLM candidate rejected 5/5 by the deterministic send guard (`_finalize_red_team_pitch`: exception-lexicon predicate) | canonical (primary) 5/5 |
| Monitor LLM verdict on the LLM candidate | — | APPROVE 4/5 (overridden to REVISE by the deterministic lexicon check), REVISE 1/5 (Pillar 1: hypothesis written as a statement) | — |
| Model calls spent on the strike | — | 2 (1 generation + 1 Monitor review), both wasted | 0 |
| Swarm turns, median [min–max] | 3 [3–3] | 3 [3–3] | 3 [2–3] |
| Model calls per run, median [min–max] | 24 [24–25] | 27 [26–28] | 24 [16–25] |
| Total tokens per run, median [min–max] | 61,472 [53,461–63,260] | 66,283 [62,062–75,031] | 56,257 [38,676–63,451] |
| Terminal outcome | CONTAMINATION_STACK (5/5) | BREAKTHROUGH_AFTER_PURGE (5/5) | BREAKTHROUGH_AFTER_PURGE (5/5) |
| May 2026 single run (reference only) | stuck (3B) | 3A Run2: failed (LLM strike, pre-fallback code) | 3A Run3: unlock after purge + canonical strike |

## Table 3 — Recovery mechanism, per Phase 3A run

| Run | Arm | Deadlock turn | Sales-side context at purge (chars) | After purge (chars) | Strike source | Strike length (chars) | Calls for strike | Gatekeeper reply to strike | Total calls |
|---|---|---|---|---|---|---|---|---|---|
| P3A_LLM_r2 | P3A'-LLM | 3 | 5,211 | 76 | LLM candidate rejected → canonical fallback | 394 | 2 | EXCEPTION_UNLOCK → MEETING_UNLOCK_APPROVED | 28 |
| P3A_LLM_r3 | P3A'-LLM | 3 | 3,997 | 76 | LLM candidate rejected → canonical fallback | 394 | 2 | EXCEPTION_UNLOCK → MEETING_UNLOCK_APPROVED | 28 |
| P3A_LLM_r4 | P3A'-LLM | 3 | 5,139 | 76 | LLM candidate rejected → canonical fallback | 394 | 2 | EXCEPTION_UNLOCK → MEETING_UNLOCK_APPROVED | 27 |
| P3A_LLM_r5 | P3A'-LLM | 3 | 4,551 | 76 | LLM candidate rejected → canonical fallback | 394 | 2 | EXCEPTION_UNLOCK → MEETING_UNLOCK_APPROVED | 26 |
| P3A_LLM_r6 | P3A'-LLM | 3 | 5,147 | 76 | LLM candidate rejected → canonical fallback | 394 | 2 | EXCEPTION_UNLOCK → MEETING_UNLOCK_APPROVED | 27 |
| P3A_CANON_r2 | P3A'-CANON | 3 | 4,801 | 76 | canonical (primary) | 394 | 0 | EXCEPTION_UNLOCK → MEETING_UNLOCK_APPROVED | 25 |
| P3A_CANON_r3 | P3A'-CANON | 3 | 4,777 | 76 | canonical (primary) | 394 | 0 | EXCEPTION_UNLOCK → MEETING_UNLOCK_APPROVED | 24 |
| P3A_CANON_r4 | P3A'-CANON | 2 | 3,340 | 76 | canonical (primary) | 394 | 0 | EXCEPTION_UNLOCK → MEETING_UNLOCK_APPROVED | 16 |
| P3A_CANON_r5 | P3A'-CANON | 3 | 4,530 | 76 | canonical (primary) | 394 | 0 | EXCEPTION_UNLOCK → MEETING_UNLOCK_APPROVED | 24 |
| P3A_CANON_r6 | P3A'-CANON | 3 | 5,022 | 76 | canonical (primary) | 394 | 0 | EXCEPTION_UNLOCK → MEETING_UNLOCK_APPROVED | 25 |

Reference, P3B' (no purge): context at deadlock 5,133, 4,119, 5,035, 5,322, 5,505 chars; run terminates (`STACK_WITHOUT_PURGE_3B`, wasted calls = 24, 25, 25, 24, 24).

## Table 4 — Monitor and Tier-3 hard-gate evidence (all events, 5 runs per configuration)

| Configuration | Monitor reviews | REVISE verdicts | Violations logged | Z-axis fail | Tier-3 PASS | Tier-3 FAIL (retried) | Max attempts | Pitches truncated to limit | Director plan fallback |
|---|---|---|---|---|---|---|---|---|---|
| P1' | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 2 | 0 |
| P2A' | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0 |
| P2B' | 14 | 4 | 6 | 2 | 14 | 1 | 2 | 4 | 0 |
| P3B' | 15 | 0 | 0 | 0 | 15 | 2 | 2 | 5 | 0 |
| P3A'-LLM | 20 | 6 | 6 | 0 | 20 | 6 | 2 | 3 | 0 |
| P3A'-CANON | 14 | 0 | 0 | 0 | 14 | 2 | 2 | 4 | 0 |

Tier-3 failure reason (all FAIL events): Value error, CRITICAL_OUTPUT_ERROR: Generated pitch text does not contain any hypothesis question mark (?). The agent failed the 'Hypothesis-driven Pain Scan' gate. Triggering instant Auto-Correction.. Every FAIL was followed by a PASS on attempt 2 (no `TIER3_HARD_GATE_EXHAUSTED`; limit 3 attempts). Mechanics (code, main `e3e1270`): Tier-3 is a Pydantic schema check (`contains_hypothesis_question = '?' in text`, 0 model calls); each FAIL triggers one rewrite call with a fix prompt (+1 call). Monitor is one model call per turn returning `verdict` + optional `revised_pitch`; on REVISE the revised text replaces the pitch in-line (`monitor_revised: true`, no extra call); BLOCK never occurred.

Monitor violations (unique texts): Pillar 1 Violation: Pitch is declarative and does not lead with the required hypothesis-driven question format (?). / Pillar 1 Violation: The opening hypothesis is a statement ('Hypothesis: ...'). It must be framed as a question to comply with the constitution and Red Team directive ('Pillar 1 hypothesis with ?'). / Pillar 1: Fails to lead with a hypothesis-driven question about analyst workload, backlog, or capacity. / Pillar 1: Pitch does not lead with a hypothesis-driven question about analyst workload; the question 'Does that work?' is for scheduling confirmation, not probing pain. / Pillar 1: Pitch is a statement, not a hypothesis-driven question about analyst workload/capacity. / Pillar 2 Violation: Positioning as 'overflow / supplemental' capacity is not explicit and only weakly implied. / Pillar 2: Fails to position the offer as overflow / supplemental research capacity. / Red Team: must include analyst pain + overflow research + Pillar-4 PoC + ? / {'pillar': 'Pillar 4', 'description': "The call to action mentions the '$3,500 PoC' but omits required framing from the PoC exception lexicon, such as 'published list rate', 'paid upfront', or explicit 'risk-reversal' framing in the final sentence. This fails to meet the strict compliance standard for Red Team mode."}

## Table 5 — Pre-registered hypotheses (RERUN_PLAN v2) and outcomes

| ID | Hypothesis | Result | Test statistic | Verdict |
|---|---|---|---|---|
| H-A | P2A' unlocks in fewer turns than P1' | turns P1' [4, 4, 4, 4, 4] vs P2A' [4, 4, 4, 4, 1]; unlock 0/5 vs 1/5 | one-sided Mann–Whitney (P2A' < P1') p = 0.35; Fisher (unlock) p = 1.00 | not supported |
| H-B | ≥40% fewer model calls (P2A' vs P1') | median 24 → 28 (reduction of medians -17%, 95% CI -17% to 71%); means 24.0 → 23.8 | one-sided Mann–Whitney p = 0.95 | not supported |
| H-C | ≥50% fewer tokens (P2A' vs P1') — first direct measurement | median 55,290 → 60,613 (reduction of medians -10%, 95% CI -23% to 73%) | one-sided Mann–Whitney p = 0.92 | not supported |
| H-D | Monitor + Tier-3 (P2B') does not lower the unlock rate vs P2A' | unlock 1/5 → 2/5; calls 28 → 32 in stuck runs (+1/turn) | Fisher two-sided p = 1.00 (one-sided 'lower' p = 0.92) | consistent (no reduction observed; low power) |
| H-E | P3B' never unlocks; P3A'-CANON unlocks | 0/5 vs 5/5 at the same call budget (median 24 vs 24) | Fisher two-sided p = 0.0079 | supported |
| H-F | P3A'-CANON unlock rate > P3A'-LLM | 5/5 vs 5/5 (pre-registered metric); LLM candidate accepted by the red-team pre-flight 0/5, canonical 5/5; extra calls LLM arm median 27 vs CANON 24 | Fisher (unlock) p = 1.00; Fisher (candidate acceptance) p = 0.0079; one-sided Mann–Whitney on calls p = 0.004 | not supported on unlock rate (fallback guard equalised the arms); supported on candidate acceptance and cost |

## Table 6 — Run ledger (30 valid runs)

| # | Config | Log | Start (UTC) | Post-PR#2 | Outcome | Turns | Calls | Prompt tok | Cand. tok | Thinking tok | Total tok | 429 retries | Unlock (turn) | Gatekeeper trajectory (mock numbering) | Notes |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | P1' | P1_r1.log | 2026-10-05 11:09 | no | POLITE_LOOP_STACK | 4 | 24 | 12,428 | 890 | 41,424 | 54,742 |  | no | T1:SOFT > T2:SOFT > T3:ACT_EXPL > T4:PROG_ESC |  |
| 2 | P1' | P1_r3.log | 2026-10-07 01:38 | yes | POLITE_LOOP_STACK | 4 | 24 | 12,161 | 923 | 42,206 | 55,290 | 0 | no | T1:SOFT > T2:SOFT > T3:ACT_EXPL > T4:PROG_ESC | truncated×1 |
| 3 | P1' | P1_r4.log | 2026-10-07 05:42 | yes | POLITE_LOOP_STACK | 4 | 24 | 12,407 | 910 | 45,188 | 58,505 | 0 | no | T1:SOFT > T2:SOFT > T3:ACT_EXPL > T4:PROG_ESC |  |
| 4 | P1' | P1_r5.log | 2026-10-08 02:10 | yes | POLITE_LOOP_STACK | 4 | 24 | 11,831 | 904 | 41,975 | 54,710 | 0 | no | T1:SOFT > T2:SOFT > T3:ACT_EXPL > T4:PROG_ESC |  |
| 5 | P1' | P1_r6_retry1.log | 2026-10-08 05:17 | yes | POLITE_LOOP_STACK | 4 | 24 | 12,605 | 913 | 41,830 | 55,348 | 1 | no | T1:SOFT > T2:SOFT > T3:ACT_EXPL > T4:PROG_ESC | truncated×1 |
| 6 | P2A' | P2A_r1.log | 2026-10-06 05:20 | no | POLITE_LOOP_STACK | 4 | 28 | 20,905 | 1,592 | 38,116 | 60,613 |  | no | T1:SOFT > T2:SOFT > T3:ACT_EXPL > T4:PROG_ESC |  |
| 7 | P2A' | P2A_r3.log | 2026-10-07 00:56 | yes | POLITE_LOOP_STACK | 4 | 28 | 21,364 | 1,698 | 41,045 | 64,107 | 0 | no | T1:SOFT > T2:SOFT > T3:ACT_EXPL > T4:PROG_ESC | truncated×1 |
| 8 | P2A' | P2A_r4.log | 2026-10-07 05:54 | yes | POLITE_LOOP_STACK | 4 | 28 | 20,878 | 1,719 | 45,161 | 67,758 | 0 | no | T1:SOFT > T2:SOFT > T3:ACT_EXPL > T4:PROG_ESC |  |
| 9 | P2A' | P2A_r5.log | 2026-10-08 02:23 | yes | POLITE_LOOP_STACK | 4 | 28 | 19,685 | 1,529 | 36,281 | 57,495 | 0 | no | T1:SOFT > T2:SOFT > T3:ACT_EXPL > T4:PROG_ESC | Gatekeeper REPLY_EXTRACTION_FALLBACK (prompt_leak_marker:internal evaluation status) |
| 10 | P2A' | P2A_r6.log | 2026-10-08 05:32 | yes | BREAKTHROUGH | 1 | 7 | 3,720 | 348 | 10,796 | 14,864 | 0 | yes (1) | T1:UNLOCK |  |
| 11 | P2B' | P2B_r2_retry1.log | 2026-10-06 10:07 | no | POLITE_LOOP_STACK | 4 | 33 | 21,803 | 1,895 | 50,483 | 74,181 |  | no | T1:SOFT > T2:SOFT > T3:ACT_EXPL > T4:PROG_ESC | Tier-3 FAIL×1→PASS; Monitor REVISE×1; truncated×1 |
| 12 | P2B' | P2B_r3.log | 2026-10-07 01:05 | yes | POLITE_LOOP_STACK | 4 | 32 | 22,586 | 1,991 | 48,329 | 72,906 | 0 | no | T1:SOFT > T2:SOFT > T3:ACT_EXPL > T4:PROG_ESC | Monitor REVISE×2; truncated×2 |
| 13 | P2B' | P2B_r4.log | 2026-10-08 00:46 | yes | BREAKTHROUGH | 1 | 8 | 4,371 | 402 | 9,852 | 14,625 | 0 | yes (1) | T1:UNLOCK |  |
| 14 | P2B' | P2B_r5.log | 2026-10-08 02:47 | yes | POLITE_LOOP_STACK | 4 | 32 | 22,838 | 1,956 | 46,665 | 71,459 | 0 | no | T1:SOFT > T2:SOFT > T3:ACT_EXPL > T4:PROG_ESC | Monitor REVISE×1; truncated×1 |
| 15 | P2B' | P2B_r6.log | 2026-10-08 05:36 | yes | BREAKTHROUGH | 1 | 8 | 4,140 | 365 | 10,488 | 14,993 | 1 | yes (1) | T1:UNLOCK |  |
| 16 | P3B' | P3B_r2.log | 2026-10-06 10:26 | no | CONTAMINATION_STACK | 3 | 24 | 19,772 | 2,499 | 40,989 | 63,260 |  | no | T1:FRAME > T2:SOFT > T3:ACT_EXPL | truncated×1 |
| 17 | P3B' | P3B_r3.log | 2026-10-07 01:57 | yes | CONTAMINATION_STACK | 3 | 25 | 18,616 | 2,407 | 40,449 | 61,472 | 0 | no | T1:SOFT > T2:FRAME > T3:ACT_EXPL | Tier-3 FAIL×1→PASS; Gatekeeper REPLY_EXTRACTION_FALLBACK (prompt_leak_marker:frustration score) |
| 18 | P3B' | P3B_r4.log | 2026-10-08 01:03 | yes | CONTAMINATION_STACK | 3 | 25 | 19,761 | 2,622 | 40,072 | 62,455 | 0 | no | T1:FRAME > T2:SOFT > T3:ACT_EXPL | Tier-3 FAIL×1→PASS |
| 19 | P3B' | P3B_r5.log | 2026-10-08 03:03 | yes | CONTAMINATION_STACK | 3 | 24 | 18,132 | 2,120 | 33,209 | 53,461 | 0 | no | T1:SOFT > T2:FRAME > T3:ACT_EXPL | truncated×2 |
| 20 | P3B' | P3B_r6.log | 2026-10-08 05:53 | yes | CONTAMINATION_STACK | 3 | 24 | 20,002 | 2,445 | 37,171 | 59,618 | 0 | no | T1:FRAME > T2:SOFT > T3:ACT_EXPL | truncated×2 |
| 21 | P3A'-LLM | P3A_LLM_r2.log | 2026-10-06 10:47 | yes | BREAKTHROUGH_AFTER_PURGE | 3 | 28 | 21,615 | 3,320 | 50,096 | 75,031 | 0 | yes (3) | T1:FRAME > T2:SOFT > T3:ACT_EXPL > T4:UNLOCK | Tier-3 FAIL×2→PASS; Monitor REVISE×2; LLM strike rejected → canonical |
| 22 | P3A'-LLM | P3A_LLM_r3.log | 2026-10-07 04:05 | yes | BREAKTHROUGH_AFTER_PURGE | 3 | 28 | 20,149 | 2,993 | 43,141 | 66,283 | 0 | yes (3) | T1:SOFT > T2:SOFT > T3:ACT_EXPL > T4:UNLOCK | Tier-3 FAIL×2→PASS; Monitor REVISE×1; LLM strike rejected → canonical |
| 23 | P3A'-LLM | P3A_LLM_r4.log | 2026-10-08 01:12 | yes | BREAKTHROUGH_AFTER_PURGE | 3 | 27 | 21,012 | 2,732 | 41,802 | 65,546 | 0 | yes (3) | T1:FRAME > T2:SOFT > T3:ACT_EXPL > T4:UNLOCK | Tier-3 FAIL×1→PASS; Monitor REVISE×1; truncated×1; LLM strike rejected → canonical |
| 24 | P3A'-LLM | P3A_LLM_r5.log | 2026-10-08 03:12 | yes | BREAKTHROUGH_AFTER_PURGE | 3 | 26 | 19,554 | 2,355 | 40,153 | 62,062 | 0 | yes (3) | T1:SOFT > T2:SOFT > T3:ACT_EXPL > T4:UNLOCK | Monitor REVISE×1; truncated×1; LLM strike rejected → canonical |
| 25 | P3A'-LLM | P3A_LLM_r6.log | 2026-10-08 06:06 | yes | BREAKTHROUGH_AFTER_PURGE | 3 | 27 | 22,144 | 2,928 | 46,276 | 71,348 | 0 | yes (3) | T1:FRAME > T2:SOFT > T3:ACT_EXPL > T4:UNLOCK | Tier-3 FAIL×1→PASS; Monitor REVISE×1; truncated×1; LLM strike rejected → canonical |
| 26 | P3A'-CANON | P3A_CANON_r2.log | 2026-10-06 11:03 | yes | BREAKTHROUGH_AFTER_PURGE | 3 | 25 | 17,849 | 2,351 | 43,251 | 63,451 | 0 | yes (3) | T1:SOFT > T2:SOFT > T3:ACT_EXPL > T4:UNLOCK | Tier-3 FAIL×1→PASS |
| 27 | P3A'-CANON | P3A_CANON_r3.log | 2026-10-07 04:16 | yes | BREAKTHROUGH_AFTER_PURGE | 3 | 24 | 17,721 | 2,068 | 35,734 | 55,523 | 0 | yes (3) | T1:SOFT > T2:SOFT > T3:ACT_EXPL > T4:UNLOCK | truncated×1 |
| 28 | P3A'-CANON | P3A_CANON_r4.log | 2026-10-08 01:35 | yes | BREAKTHROUGH_AFTER_PURGE | 2 | 16 | 10,969 | 1,584 | 26,123 | 38,676 | 0 | yes (2) | T1:FRAME > T2:SOFT > T3:UNLOCK | truncated×1; NDA URL surfaced at msg 2 |
| 29 | P3A'-CANON | P3A_CANON_r5.log | 2026-10-08 03:23 | yes | BREAKTHROUGH_AFTER_PURGE | 3 | 24 | 18,027 | 2,172 | 36,058 | 56,257 | 0 | yes (3) | T1:SOFT > T2:SOFT > T3:ACT_EXPL > T4:UNLOCK | truncated×1 |
| 30 | P3A'-CANON | P3A_CANON_r6.log | 2026-10-08 06:19 | yes | BREAKTHROUGH_AFTER_PURGE | 3 | 25 | 18,997 | 2,470 | 40,410 | 61,877 | 0 | yes (3) | T1:SOFT > T2:SOFT > T3:ACT_EXPL > T4:UNLOCK | Tier-3 FAIL×1→PASS; truncated×1 |

## Table 7 — Excluded attempts

| Log / thread | Config | Start (UTC) | What happened | Disposition |
|---|---|---|---|---|
| P2B_r2.log | P2B' | 2026-10-06 06:39 | Sales-side Gemini 429 (ResourceExhausted) raised at turn 3 before `STUDY_COMPLETE` (pre-PR#2 code without retry); 2 Gatekeeper exchanges completed (SOFT_REJECT, SOFT_REJECT) | invalid; log retained; configuration re-run (P2B_r2_retry1) |
| P1_r6.log | P1' | 2026-10-08 03:44 | Cloud Shell metadata server returned 503 ('service account info is missing email field'); 5 retries, no Gatekeeper exchange | invalid; log retained; configuration re-run (P1_r6_retry1) |
| Gatekeeper thread tx_phase2b_monitor_on_98154740 | P2B'-type (thread id prefix phase2b_monitor_on) | 2026-10-06 09:58 | 4 exchanges recorded on the Gatekeeper side (T1:SOFT_REJECT > T2:SOFT_REJECT > T3:ACTIVE_EXPLOITATION > T4:PROGRESSIVE_ESCALATION); Sales-side run interrupted by the operator, no Sales-side log retained | disclosed; counted in the conservative unlock rate (no unlock; calls/tokens unknown) |
| Gatekeeper thread tx_phase2b_monitor_on_af0b9782 | P2B'-type (thread id prefix phase2b_monitor_on) | 2026-10-07 09:00 | 4 exchanges recorded on the Gatekeeper side (T1:SOFT_REJECT > T2:SOFT_REJECT > T3:ACTIVE_EXPLOITATION > T4:PROGRESSIVE_ESCALATION); Sales-side run interrupted by the operator, no Sales-side log retained | disclosed; counted in the conservative unlock rate (no unlock; calls/tokens unknown) |
| Gatekeeper thread tx_phase1_baseline_3896911a | P1'-type (thread id prefix phase1_baseline) | 2026-10-08 03:34 | 4 exchanges recorded on the Gatekeeper side (T1:SOFT_REJECT > T2:SOFT_REJECT > T3:ACTIVE_EXPLOITATION > T4:PROGRESSIVE_ESCALATION); Sales-side run interrupted by the operator, no Sales-side log retained | disclosed; counted in the conservative unlock rate (no unlock; calls/tokens unknown) |

## Table 8 — Execution conditions

| Item | Value |
|---|---|
| Sales-side model | gemini-2.5-pro (Vertex AI, us-central1), `gemini_model_version` identical in all 724 usage records |
| Gatekeeper model | claude-haiku-4-5 (Vertex AI, us-east5), `gatekeeper_llm_mode = vertex` at all 18 mock-server starts; all 119 rawPredict calls HTTP 200 |
| Gatekeeper acceptance logic | deterministic regular-expression state machine (unchanged since May 2026); LLM generates reply text only |
| Code | `0x-AO-Protocol/ao_system_openclaw` main `e3e1270` (PR #2) for 26 runs; `ce6d198` (PR #1) for the 4 earliest runs (P1_r1, P2A_r1, P2B_r2_retry1, P3B_r2), identified mechanically by the absence of `gemini_429_retries` in `STUDY_COMPLETE` |
| Character limits / max turns | 300 (Phase 1–2), 1,000 (Phase 3); `max_turns` = 8 (never reached: every non-unlocked run terminated by deadlock detection at turn 3 or 4) |
| Time span | 2026-10-05 11:09 → 2026-10-08 06:26 UTC; 216 min of wall-clock across 30 runs |
| Totals | 724 Gemini calls, 1,707,916 tokens |
| Integrity | 30/30 `STUDY_COMPLETE`; 0 `STUDY_ERROR`; 0 tracebacks; per-call usage sums equal `STUDY_COMPLETE` totals in 30/30; Gatekeeper-side exchange count and unlock verdict equal the Sales-side records in 30/30 |
| Gemini 429 retries (PR #2 telemetry) | 2 runs × 1 retry (P1_r6_retry1, P2B_r6); retries do not alter prompts or verdicts |
| Gatekeeper reply-extraction fallback | 2 events (P2A_r5 msg 3, P3B_r3 msg 3): the LLM reply leaked an internal marker and was replaced by the rule-based canned text; the status decision was unaffected |
| Dependencies | `pip_freeze_2026-10.txt` in the log archive |
