# Constitutional Gating and Deterministic Recovery — testbed, logs and analysis

Code, run logs and analysis scripts for:

> Masaaki Nakatsu and Reno Wang. 2026. *Constitutional Gating and Deterministic Recovery for Multi-Agent LLM Negotiation: Ablations Against a Stateful Adversarial Gatekeeper.* arXiv:2610.11542 [cs.CL]. https://arxiv.org/abs/2610.11542

Companion paper: *Decoupling Logic from Persona: Structural Immunity of Edge LLM Agents to Context Pollution*, arXiv:2610.09772.

Everything needed to recompute every table, statistic and figure in the paper from the raw logs is in this repository and runs without any API key. Re-running the experiment itself requires Google Cloud (Vertex AI).

## Contents

| Path | What it is |
|---|---|
| `mock_adversarial_target.py` | The stateful adversarial Gatekeeper (FastAPI, port 8080): regular-expression classifier, hidden state machine, forced honeytrap, acceptance rules, status-specific prompts and canned replies. Its LLM only renders reply text. |
| `phase3_exception_lexicon_openclaw.py` | Phase 3 exception lexicon shared by the Gatekeeper and the agents (Pillar-4 proof-of-concept terms, analyst fatigue, discount language). |
| `brain_cloud_openclaw/agents/phase1_baseline_agent_openclaw.py` | Arm P1': three-agent debate and majority vote, no constitution. |
| `brain_cloud_openclaw/agents/phase2_five_pillar_agent_openclaw.py` | Arms P2A' and P2B': 5-Pillar constitution, Director, optional Monitor and Tier-3 hard gate. |
| `brain_cloud_openclaw/agents/phase3_hybrid_agent_openclaw.py` | Arms P3B', P3A'-LLM and P3A'-CANON: deadlock detector, atomic purge, red-team strike and send guard. |
| `brain_cloud_openclaw/agents/gemini_retry.py` | Retry-with-backoff wrapper for agent-side Gemini calls (HTTP 429/503). |
| `brain_cloud_openclaw/schemas_openclaw.py` | Pydantic schema used by the Tier-3 hard gate. |
| `tests/` | Unit tests (17; no cloud access needed). |
| `test_claude_connection.py`, `test_gemini_connection.py` | Connectivity checks run before the study. |
| `requirements-adversarial.txt` | Runtime dependencies. Exact versions used: `logs/rerun_2026-10/pip_freeze_2026-10.txt`. |
| `docs/RUNBOOK_paper2_rerun.md` | How the 30 runs were executed. |
| `logs/` | All run logs (see `logs/README.md`). |
| `analysis/` | Scripts that turn the logs into the paper's tables, statistics and figures, and their outputs in `analysis/out/`. |

## Reproduce the paper's numbers (no API key needed)

```bash
python3 -m venv .venv && . .venv/bin/activate
pip install -r analysis/requirements-analysis.txt
bash analysis/run_all.sh
git status --short analysis/out     # prints nothing with the tested versions below
```

| Output in `analysis/out/` | In the paper |
|---|---|
| `tables.md`, Table 1 | Table 3 (Phase 1 to 2B) |
| `tables.md`, Table 2 | Table 4 (Phase 3) |
| `tables.md`, Table 4 | Table 5 (Monitor and hard-gate events) |
| `tables.md`, Table 5 | Table 6 (pre-registered hypotheses) |
| `tables.md`, Tables 6–8 | Appendix A.1, Section 5.7, Section 4.5 |
| `lexicon_hits.md` | Table 3, row "Messages meeting the acceptance lexicon"; Section 5.2 trajectory counts |
| `stats.json` | All test statistics, intervals and descriptive figures quoted in Sections 5.1–5.5 |
| `figs/fig3_control_stack.pdf` | Figure 1 |
| `figs/fig1_metrics_by_config.pdf` | Figure 2 |
| `figs/fig2_state_trajectories.pdf` | Figure 3 |
| `appendix_generated.md` | Appendix A (run ledger and event timelines) |
| `ledger_runs.csv`, `turns.csv`, `mock_threads.csv`, `consistency.csv` | Per-run ledger, per-turn table, Gatekeeper-side records, integrity checks (Section 5.7) |

Tested with Python 3.13, numpy 2.5, pandas 3.0, scipy 1.18 and matplotlib 3.11. Bootstrap intervals use a fixed seed, and figure timestamps are fixed, so a rerun is byte-identical.

## Re-run the experiment (Google Cloud required)

Two processes talk over HTTP: the Gatekeeper mock and one sales agent per run.

- Agents: Gemini 2.5 Pro on Vertex AI, `us-central1`.
- Gatekeeper reply text: Claude Haiku 4.5 on Vertex AI, `us-east5` (`AO_GATEKEEPER_LLM_MODE=vertex`). The acceptance decision never depends on this model.
- Set `AO_GCP_PROJECT_ID` to your own project. The defaults in the code name the authors' project and will not work for you.

Step-by-step commands, environment variables for all six arms and the checks made at each step are in `docs/RUNBOOK_paper2_rerun.md`. Run the unit tests with `python -m pytest tests/ -q`.

Model outputs differ between runs, so a re-run will not reproduce the logs line for line. The Gatekeeper's acceptance decision for a given message is deterministic.

## Provenance

This repository is a snapshot of the authors' internal repository at commit `e3e1270` (2026-10-06). Every code file listed under Contents is byte-identical to that commit; the git blob IDs are:

| File | Blob at `e3e1270` |
|---|---|
| `mock_adversarial_target.py` | `208459e2eafbbc6d2a795481ecc02d6ccb2a8bed` |
| `phase3_exception_lexicon_openclaw.py` | `53e7e8df512914c142319ce178bc36c1a11ff429` |
| `brain_cloud_openclaw/agents/gemini_retry.py` | `b7a541079765ea8b130c20aa33ec1fe24a1557ac` |
| `brain_cloud_openclaw/agents/phase1_baseline_agent_openclaw.py` | `2d483ff98888815ac289df4c9ef1275316f229ee` |
| `brain_cloud_openclaw/agents/phase2_five_pillar_agent_openclaw.py` | `cf4b35eddc8c3327260659d9d31ef727733c4757` |
| `brain_cloud_openclaw/agents/phase3_hybrid_agent_openclaw.py` | `4da1791b1ee9fc14a4578f24f6948ddf3ea5be28` |
| `brain_cloud_openclaw/schemas_openclaw.py` | `01f0d21207c7afdf4ad30029fb9a763e2916ae66` |
| `requirements-adversarial.txt` | `69fd50e0c5ff98500f8fbebbaa827b30e27503eb` |
| `test_claude_connection.py` | `de0dfb448e0a4816e9dd291f1bbd599243f88292` |
| `test_gemini_connection.py` | `a1895eb02098f71ef4dc25612bb747972a71d9dd` |
| `tests/test_director_context_defaults.py` | `aeac92f97f8fc6d03fe295499f550574bc9ed507` |
| `tests/test_gemini_retry.py` | `4ab6bc0e11d876d905116a9827858f43299b82c9` |
| `tests/test_gemini_usage_telemetry.py` | `1b2c2dc96e015fe0f7d7ede9253ccf38f6455f51` |
| `tests/test_llama_reply_extraction.py` | `2fbcadf781dc3ecd574d04633c1ef558dba3766b` |

The four earliest runs used the preceding commit `ce6d198`. The only difference is the retry wrapper: `gemini_retry.py` and its test were added, and the three agent files gained the import, the wrapped call sites and a `gemini_429_retries` field in the summary record. Prompts, constitution, lexicon and verdict logic are unchanged (paper, Section 4.5).

Not included from the internal repository: two files that belong to a different prototype and play no part in the paper (an integration agent and an API server), a duplicate of `schemas_openclaw.py` without a file extension, the internal working README and pull-request description, and the operator's runbook, which was written in Japanese and is replaced here by an English translation with project-specific identifiers replaced by placeholders.

## Citation

```bibtex
@misc{nakatsu2026constitutional,
  title         = {Constitutional Gating and Deterministic Recovery for Multi-Agent {LLM} Negotiation: Ablations Against a Stateful Adversarial Gatekeeper},
  author        = {Nakatsu, Masaaki and Wang, Reno},
  year          = {2026},
  eprint        = {2610.11542},
  archivePrefix = {arXiv},
  primaryClass  = {cs.CL}
}

@misc{nakatsu2026decoupling,
  title         = {Decoupling Logic from Persona: Structural Immunity of Edge {LLM} Agents to Context Pollution},
  author        = {Nakatsu, Masaaki and Wang, Reno},
  year          = {2026},
  eprint        = {2610.09772},
  archivePrefix = {arXiv},
  primaryClass  = {cs.CL}
}
```

## Licence

Code and analysis scripts: MIT (see `LICENSE`). The logs contain text generated by Gemini 2.5 Pro and Claude Haiku 4.5; use of those models and their outputs is subject to the providers' terms.
