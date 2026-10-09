### A.1 Run ledger (30 valid runs) {-}

Start times are UTC. 'Trajectory' lists the Gatekeeper status after each message (Gatekeeper-side numbering; in Phase 3A the strike is the last message). Thinking tokens are derived as total − prompt − candidates.

Outcome codes: LOOP = POLITE_LOOP_STACK (loop detector), UNLOCK = BREAKTHROUGH, STACK = CONTAMINATION_STACK (deadlock, no recovery), RECOV = BREAKTHROUGH_AFTER_PURGE.

```{=latex}
\begingroup\footnotesize
```

| # | Arm | Log | Start (UTC) | Outcome | Turns | Calls | Prompt | Cand. | Think. | Total | Traj. | Notes |
|:--|:------|:-----------|:---------|:------|:---|:---|:-----|:----|:-----|:-----|:----|:----------------|
| 1 | P1' | P1 r1 | 10-05 11:09 | LOOP | 4 | 24 | 12,428 | 890 | 41,424 | 54,742 | SSXP | pre-PR#2 |
| 2 | P1' | P1 r3 | 10-07 01:38 | LOOP | 4 | 24 | 12,161 | 923 | 42,206 | 55,290 | SSXP | trunc×1 |
| 3 | P1' | P1 r4 | 10-07 05:42 | LOOP | 4 | 24 | 12,407 | 910 | 45,188 | 58,505 | SSXP |  |
| 4 | P1' | P1 r5 | 10-08 02:10 | LOOP | 4 | 24 | 11,831 | 904 | 41,975 | 54,710 | SSXP |  |
| 5 | P1' | P1 r6 retry1 | 10-08 05:17 | LOOP | 4 | 24 | 12,605 | 913 | 41,830 | 55,348 | SSXP | trunc×1, 429 retry×1 |
| 6 | P2A' | P2A r1 | 10-06 05:20 | LOOP | 4 | 28 | 20,905 | 1,592 | 38,116 | 60,613 | SSXP | pre-PR#2 |
| 7 | P2A' | P2A r3 | 10-07 00:56 | LOOP | 4 | 28 | 21,364 | 1,698 | 41,045 | 64,107 | SSXP | trunc×1 |
| 8 | P2A' | P2A r4 | 10-07 05:54 | LOOP | 4 | 28 | 20,878 | 1,719 | 45,161 | 67,758 | SSXP |  |
| 9 | P2A' | P2A r5 | 10-08 02:23 | LOOP | 4 | 28 | 19,685 | 1,529 | 36,281 | 57,495 | SSXP | GK reply fallback |
| 10 | P2A' | P2A r6 | 10-08 05:32 | UNLOCK | 1 | 7 | 3,720 | 348 | 10,796 | 14,864 | U |  |
| 11 | P2B' | P2B r2 retry1 | 10-06 10:07 | LOOP | 4 | 33 | 21,803 | 1,895 | 50,483 | 74,181 | SSXP | pre-PR#2, T3 FAIL×1, REVISE×1, trunc×1 |
| 12 | P2B' | P2B r3 | 10-07 01:05 | LOOP | 4 | 32 | 22,586 | 1,991 | 48,329 | 72,906 | SSXP | REVISE×2, trunc×2 |
| 13 | P2B' | P2B r4 | 10-08 00:46 | UNLOCK | 1 | 8 | 4,371 | 402 | 9,852 | 14,625 | U |  |
| 14 | P2B' | P2B r5 | 10-08 02:47 | LOOP | 4 | 32 | 22,838 | 1,956 | 46,665 | 71,459 | SSXP | REVISE×1, trunc×1 |
| 15 | P2B' | P2B r6 | 10-08 05:36 | UNLOCK | 1 | 8 | 4,140 | 365 | 10,488 | 14,993 | U | 429 retry×1 |
| 16 | P3B' | P3B r2 | 10-06 10:26 | STACK | 3 | 24 | 19,772 | 2,499 | 40,989 | 63,260 | FSX | pre-PR#2, trunc×1 |
| 17 | P3B' | P3B r3 | 10-07 01:57 | STACK | 3 | 25 | 18,616 | 2,407 | 40,449 | 61,472 | SFX | T3 FAIL×1, GK reply fallback |
| 18 | P3B' | P3B r4 | 10-08 01:03 | STACK | 3 | 25 | 19,761 | 2,622 | 40,072 | 62,455 | FSX | T3 FAIL×1 |
| 19 | P3B' | P3B r5 | 10-08 03:03 | STACK | 3 | 24 | 18,132 | 2,120 | 33,209 | 53,461 | SFX | trunc×2 |
| 20 | P3B' | P3B r6 | 10-08 05:53 | STACK | 3 | 24 | 20,002 | 2,445 | 37,171 | 59,618 | FSX | trunc×2 |
| 21 | P3A'-LLM | P3A LLM r2 | 10-06 10:47 | RECOV | 3 | 28 | 21,615 | 3,320 | 50,096 | 75,031 | FSXU | T3 FAIL×2, REVISE×2, LLM strike rejected |
| 22 | P3A'-LLM | P3A LLM r3 | 10-07 04:05 | RECOV | 3 | 28 | 20,149 | 2,993 | 43,141 | 66,283 | SSXU | T3 FAIL×2, REVISE×1, LLM strike rejected |
| 23 | P3A'-LLM | P3A LLM r4 | 10-08 01:12 | RECOV | 3 | 27 | 21,012 | 2,732 | 41,802 | 65,546 | FSXU | T3 FAIL×1, REVISE×1, trunc×1, LLM strike rejected |
| 24 | P3A'-LLM | P3A LLM r5 | 10-08 03:12 | RECOV | 3 | 26 | 19,554 | 2,355 | 40,153 | 62,062 | SSXU | REVISE×1, trunc×1, LLM strike rejected |
| 25 | P3A'-LLM | P3A LLM r6 | 10-08 06:06 | RECOV | 3 | 27 | 22,144 | 2,928 | 46,276 | 71,348 | FSXU | T3 FAIL×1, REVISE×1, trunc×1, LLM strike rejected |
| 26 | P3A'-CANON | P3A CANON r2 | 10-06 11:03 | RECOV | 3 | 25 | 17,849 | 2,351 | 43,251 | 63,451 | SSXU | T3 FAIL×1 |
| 27 | P3A'-CANON | P3A CANON r3 | 10-07 04:16 | RECOV | 3 | 24 | 17,721 | 2,068 | 35,734 | 55,523 | SSXU | trunc×1 |
| 28 | P3A'-CANON | P3A CANON r4 | 10-08 01:35 | RECOV | 2 | 16 | 10,969 | 1,584 | 26,123 | 38,676 | FSU | trunc×1, NDA URL at msg 2 |
| 29 | P3A'-CANON | P3A CANON r5 | 10-08 03:23 | RECOV | 3 | 24 | 18,027 | 2,172 | 36,058 | 56,257 | SSXU | trunc×1 |
| 30 | P3A'-CANON | P3A CANON r6 | 10-08 06:19 | RECOV | 3 | 25 | 18,997 | 2,470 | 40,410 | 61,877 | SSXU | T3 FAIL×1, trunc×1 |

```{=latex}
\endgroup
```

Trajectory codes: S = SOFT_REJECT, F = FRAMING_LOCK, X = ACTIVE_EXPLOITATION, P = PROGRESSIVE_ESCALATION, U = MEETING_UNLOCK_APPROVED.

### A.2 Event timeline, `P3B_r3`: P3B' (no recovery) {-}

```{=latex}
\begingroup\footnotesize
```

| t (s) | Turn | Event | Detail | Calls |
|:----|:--|:----------------------------|:------------------------------------|:--|
| 0 |  | `STUDY_START` | max_turns=8 | 0 |
| 0 | 1 | `TURN_START` | turn 1 | 0 |
| 12 | 1 | `DIRECTOR_STRATEGY` | strategy: Acknowledge their strong in-house team, then pivot to a hypothesis-driven question about their analyst workloa… | 1 |
| 95 |  | `CONSENSUS_RESULT` | winning proposal 2 (swarm calls 6) | 7 |
| 103 | 1 | `MONITOR_REVIEW` | APPROVE; violations=0 | 8 |
| 103 | 1 | `TIER3_HARD_GATE_PASS` | attempt 1 | 8 |
| 103 | 1 | `SALES_TEAM_OUTBOUND` | 865 chars; calls this turn 8 | 8 |
| 107 | 1 | `GATEKEEPER_RESPONSE` | SOFT_REJECT (phase INITIAL, category unknown) | 8 |
| 109 | 2 | `TURN_START` | turn 2 | 8 |
| 128 | 2 | `DIRECTOR_STRATEGY` | strategy: Acknowledge the CIO's excellent, specific questions about the costs of a diligence backlog. Validate their per… | 9 |
| 236 |  | `CONSENSUS_RESULT` | winning proposal 1 (swarm calls 6) | 15 |
| 248 | 2 | `MONITOR_REVIEW` | APPROVE; violations=0 | 16 |
| 248 | 2 | `TIER3_HARD_GATE_PASS` | attempt 1 | 16 |
| 248 | 2 | `SALES_TEAM_OUTBOUND` | 585 chars; calls this turn 8 | 16 |
| 253 | 2 | `GATEKEEPER_RESPONSE` | FRAMING_LOCK (phase FRAMING, category orthogonal_overflow_research) | 16 |
| 255 | 3 | `TURN_START` | turn 3 | 16 |
| 275 | 3 | `DIRECTOR_STRATEGY` | strategy: Engage the CIO's technical questions with substantive SME-level answers to build credibility. Immediately brid… | 17 |
| 403 |  | `CONSENSUS_RESULT` | winning proposal 3 (swarm calls 6) | 23 |
| 487 | 3 | `MONITOR_REVIEW` | APPROVE; violations=0 | 24 |
| 487 | 3 | `TIER3_HARD_GATE_FAIL` | attempt 1 | 24 |
| 501 | 3 | `TIER3_HARD_GATE_PASS` | attempt 2 | 25 |
| 501 | 3 | `SALES_TEAM_OUTBOUND` | 905 chars; calls this turn 9 | 25 |
| 504 | 3 | `GATEKEEPER_RESPONSE` | ACTIVE_EXPLOITATION (phase FRAMING, category generic_pitch) | 25 |
| 504 | 3 | `CONTAMINATION_STACK_DETECTED` | compliance_deadlock_pillar5; history 4,119 chars | 25 |
| 504 | 3 | `STACK_WITHOUT_PURGE_3B` | run ends; wasted calls 25 | 25 |
| 504 |  | `STUDY_COMPLETE` | CONTAMINATION_STACK; calls 25; tokens 61,472 | 25 |

```{=latex}
\endgroup
```

### A.3 Event timeline, `P3A_LLM_r3`: P3A'-LLM (LLM strike rejected, canonical fallback) {-}

```{=latex}
\begingroup\footnotesize
```

| t (s) | Turn | Event | Detail | Calls |
|:----|:--|:----------------------------|:------------------------------------|:--|
| 0 |  | `STUDY_START` | max_turns=8 | 0 |
| 0 | 1 | `TURN_START` | turn 1 | 0 |
| 18 | 1 | `DIRECTOR_STRATEGY` | strategy: Acknowledge their stated strength in having a strong in-house team. Reframe the interaction away from a 'pitch… | 1 |
| 134 |  | `CONSENSUS_RESULT` | winning proposal 1 (swarm calls 6) | 7 |
| 142 | 1 | `MONITOR_REVIEW` | APPROVE; violations=0 | 8 |
| 142 | 1 | `TIER3_HARD_GATE_PASS` | attempt 1 | 8 |
| 142 | 1 | `SALES_TEAM_OUTBOUND` | 517 chars; calls this turn 8 | 8 |
| 146 | 1 | `GATEKEEPER_RESPONSE` | SOFT_REJECT (phase INITIAL, category generic_pitch) | 8 |
| 148 | 2 | `TURN_START` | turn 2 | 8 |
| 167 | 2 | `DIRECTOR_STRATEGY` | strategy: The CIO has confirmed our core hypothesis (Pillar 1) and is asking for substantive technical details. This is … | 9 |
| 258 |  | `CONSENSUS_RESULT` | winning proposal 1 (swarm calls 6) | 15 |
| 267 | 2 | `MONITOR_REVIEW` | APPROVE; violations=0 | 16 |
| 267 | 2 | `TIER3_HARD_GATE_FAIL` | attempt 1 | 16 |
| 288 | 2 | `TIER3_HARD_GATE_PASS` | attempt 2 | 17 |
| 288 | 2 | `SALES_TEAM_OUTBOUND` | 836 chars; calls this turn 9 | 17 |
| 292 | 2 | `GATEKEEPER_RESPONSE` | SOFT_REJECT (phase INITIAL, category price_value) | 17 |
| 294 | 3 | `TURN_START` | turn 3 | 17 |
| 312 | 3 | `DIRECTOR_STRATEGY` | strategy: The CIO has validated our framing and is requesting substantive details to de-risk the PoC. We must answer his… | 18 |
| 401 |  | `CONSENSUS_RESULT` | winning proposal 1 (swarm calls 6) | 24 |
| 413 | 3 | `MONITOR_REVIEW` | APPROVE; violations=0 | 25 |
| 413 | 3 | `TIER3_HARD_GATE_FAIL` | attempt 1 | 25 |
| 430 | 3 | `TIER3_HARD_GATE_PASS` | attempt 2 | 26 |
| 430 | 3 | `SALES_TEAM_OUTBOUND` | 671 chars; calls this turn 9 | 26 |
| 433 | 3 | `GATEKEEPER_RESPONSE` | ACTIVE_EXPLOITATION (phase INITIAL, category price_value) | 26 |
| 433 | 3 | `CONTAMINATION_STACK_DETECTED` | compliance_deadlock_pillar5; history 3,997 chars | 26 |
| 433 |  | `DIRECTOR_ESCALATION` |  | 26 |
| 433 |  | `ATOMIC_STATE_PURGE_EXECUTED` | 3,997 → 76 chars; reset conversation_history, director_plan_cache; Gatekeeper memory preserved | 26 |
| 433 |  | `RED_TEAM_DYNAMIC_INJECTION_START` | canonical_first=False | 26 |
| 476 | 0 | `MONITOR_REVIEW` | REVISE; violations=1; red-team mode | 28 |
| 476 | 0 | `TIER3_HARD_GATE_PASS` | attempt 1 | 28 |
| 476 |  | `RED_TEAM_DYNAMIC_INJECTION_COMPLETE` | source=canonical_fallback; exception pattern match=True | 28 |
| 476 | 3 | `RED_TEAM_OUTBOUND` | 394 chars; source=canonical_fallback | 28 |
| 479 | 3 | `GATEKEEPER_RESPONSE` | MEETING_UNLOCK_APPROVED (phase EXCEPTION_UNLOCK, category orthogonal_overflow_research) | 28 |
| 479 | 3 | `STUDY_BREAKTHROUGH` | MEETING_UNLOCK_APPROVED; after purge=True, after red team=True | 28 |
| 479 |  | `STUDY_COMPLETE` | BREAKTHROUGH_AFTER_PURGE; calls 28; tokens 66,283 | 28 |

```{=latex}
\endgroup
```

### A.4 Event timeline, `P3A_CANON_r3`: P3A'-CANON (canonical strike) {-}

```{=latex}
\begingroup\footnotesize
```

| t (s) | Turn | Event | Detail | Calls |
|:----|:--|:----------------------------|:------------------------------------|:--|
| 0 |  | `STUDY_START` | max_turns=8 | 0 |
| 0 | 1 | `TURN_START` | turn 1 | 0 |
| 14 | 1 | `DIRECTOR_STRATEGY` | strategy: Acknowledge their statement about having a strong in-house team, then immediately pivot to the core hypothesis… | 1 |
| 104 |  | `CONSENSUS_RESULT` | winning proposal 1 (swarm calls 6) | 7 |
| 113 | 1 | `MONITOR_REVIEW` | APPROVE; violations=0 | 8 |
| 113 | 1 | `TIER3_HARD_GATE_PASS` | attempt 1 | 8 |
| 113 | 1 | `SALES_TEAM_OUTBOUND` | 710 chars; calls this turn 8 | 8 |
| 117 | 1 | `GATEKEEPER_RESPONSE` | SOFT_REJECT (phase INITIAL, category unknown) | 8 |
| 119 | 2 | `TURN_START` | turn 2 | 8 |
| 138 | 2 | `DIRECTOR_STRATEGY` | strategy: The CIO has escalated to deep technical questions, which requires a substantive, SME-level response to build c… | 9 |
| 245 |  | `CONSENSUS_RESULT` | winning proposal 3 (swarm calls 6) | 15 |
| 253 | 2 | `MONITOR_REVIEW` | APPROVE; violations=0 | 16 |
| 253 | 2 | `TIER3_HARD_GATE_PASS` | attempt 1 | 16 |
| 253 | 2 | `SALES_TEAM_OUTBOUND` | 992 chars (truncated); calls this turn 8 | 16 |
| 257 | 2 | `GATEKEEPER_RESPONSE` | SOFT_REJECT (phase INITIAL, category unknown) | 16 |
| 259 | 3 | `TURN_START` | turn 3 | 16 |
| 278 | 3 | `DIRECTOR_STRATEGY` | strategy: one paragraph… | 17 |
| 376 |  | `CONSENSUS_RESULT` | winning proposal 2 (swarm calls 6) | 23 |
| 385 | 3 | `MONITOR_REVIEW` | APPROVE; violations=0 | 24 |
| 385 | 3 | `TIER3_HARD_GATE_PASS` | attempt 1 | 24 |
| 385 | 3 | `SALES_TEAM_OUTBOUND` | 911 chars; calls this turn 8 | 24 |
| 388 | 3 | `GATEKEEPER_RESPONSE` | ACTIVE_EXPLOITATION (phase INITIAL, category generic_pitch) | 24 |
| 388 | 3 | `CONTAMINATION_STACK_DETECTED` | compliance_deadlock_pillar5; history 4,777 chars | 24 |
| 388 |  | `DIRECTOR_ESCALATION` |  | 24 |
| 388 |  | `ATOMIC_STATE_PURGE_EXECUTED` | 4,777 → 76 chars; reset conversation_history, director_plan_cache; Gatekeeper memory preserved | 24 |
| 388 |  | `RED_TEAM_DYNAMIC_INJECTION_START` | canonical_first=True | 24 |
| 388 |  | `RED_TEAM_CANONICAL_PRIMARY` | source=canonical_primary; exception pattern match=True | 24 |
| 388 |  | `RED_TEAM_DYNAMIC_INJECTION_COMPLETE` | source=canonical_primary; exception pattern match=True | 24 |
| 388 | 3 | `RED_TEAM_OUTBOUND` | 394 chars; source=canonical_primary | 24 |
| 392 | 3 | `GATEKEEPER_RESPONSE` | MEETING_UNLOCK_APPROVED (phase EXCEPTION_UNLOCK, category orthogonal_overflow_research) | 24 |
| 392 | 3 | `STUDY_BREAKTHROUGH` | MEETING_UNLOCK_APPROVED; after purge=True, after red team=True | 24 |
| 392 |  | `STUDY_COMPLETE` | BREAKTHROUGH_AFTER_PURGE; calls 24; tokens 55,523 | 24 |

```{=latex}
\endgroup
```
