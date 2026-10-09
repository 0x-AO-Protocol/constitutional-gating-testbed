# May 2026 single runs

One run per configuration on 29–30 May 2026, before the pre-registered re-run. The Gatekeeper's reply text was written by Llama-3.1-8B-Instruct on a Vertex AI endpoint that has since been deleted; the agents used Gemini 2.5 Pro. The code differed from the October snapshot in the fixes listed in the paper's Appendix E. The paper compares these runs with the re-run in Section 5.6.

<!-- RAW-LOGS-STATUS -->
**Raw log files.** The runs were executed in Cloud Shell with their output written to `/tmp`, and the raw files were not retained.
<!-- /RAW-LOGS-STATUS -->

**`excerpts_from_may_report.jsonl`** holds the 353 JSON log lines that the operator copied into the internal May 2026 report while the runs were analysed, in the order they appear there and unchanged. Three further copied lines were cut off mid-object and are omitted. These are excerpts, not complete logs: for some runs most events were copied, for others only the configuration, the Gatekeeper exchanges and the summary record. The lines cover these runs:

| Transaction ID | Configuration |
|---|---|
| `tx_phase1_baseline_b8b22f91` | Phase 1 baseline |
| `tx_phase2a_monitor_off_b7795798` | Phase 2A (Monitor and hard gate off) |
| `tx_phase2b_monitor_on_919de0f4` | Phase 2B (Monitor and hard gate on) |
| `tx_phase3b_purge_off_3629da98` | Phase 3B (no recovery) |
| `tx_phase3a_purge_on_24f47025` | Phase 3A, purge on, LLM strike |
| `tx_phase3a_run3_4c066606` | Phase 3A Run 3, purge on, canonical strike |

Lines whose `transaction_id` is absent belong to the run whose lines surround them; agent-side events carry a `telemetry_type` of `PHASE1_BASELINE`, `PHASE2_FIVE_PILLAR` or `PHASE3_HYBRID`, and Gatekeeper-side events carry the `thread_id`.
