# Logs

## October 2026 re-run (the 30 runs analysed in the paper)

`logs_paper2_rerun_2026-10_anon.tgz` is the archive cited in the paper (Appendix F):

- SHA-256 of this archive: `d509fc28fef62e876bcf2b39114d7c44f9de41ec49fd99e2f945fbd874b7d7f6`
- It is the operator's raw archive (SHA-256 `0c1fa15a4372dda05793ec5efe306600e9d76f89c687f640c039da52406b11c6`, not published) with the operator's home-directory prefix replaced by `/home/user/` in 119 places and nothing else changed (`analysis/anonymize_logs.py`).

`rerun_2026-10/` holds the same 37 files, extracted so they can be read on GitHub:

| File | Content |
|---|---|
| `P1_r*.log`, `P2A_r*.log`, `P2B_r*.log`, `P3B_r*.log`, `P3A_LLM_r*.log`, `P3A_CANON_r*.log` | Agent-side logs (one JSON event per line, plus stderr). `_r<n>` is the operator's round label; not every arm has every label. |
| `P2B_r2.log`, `P1_r6.log` | The two invalid attempts, excluded from the analysis: an agent-side crash on a rate limit before the retry wrapper existed, and a credential failure before any exchange. |
| `P2B_r2_retry1.log`, `P1_r6_retry1.log` | The valid repeats of those two attempts. |
| `mock_phase2.log`, `mock_phase3.log` | Gatekeeper-side logs, one thread per run (`thread_id` = the run's `transaction_id`). They also contain the three interrupted attempts that have no agent-side log (paper, Section 5.7). Which file and thread belong to which run is listed in `analysis/out/mock_threads.csv`. |
| `smoke_A.log`, `smoke_B.log` | Smoke test before the study (Gatekeeper side and agent side); not part of the analysis. |
| `pip_freeze_2026-10.txt` | Python package versions in the environment that ran the study. |

The 30 valid runs and the excluded attempts are listed in `analysis/out/ledger_runs.csv` and `analysis/out/ledger_invalid.csv`.

## May 2026 single runs

See `may_2026_single_runs/README.md`.
