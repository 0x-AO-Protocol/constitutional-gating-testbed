# Runbook: the October 2026 re-run (30 runs)

English translation of the operator's runbook for the 30 runs analysed in the paper. Project-specific identifiers are replaced by placeholders: `<your-project>` (Google Cloud project) and `<your-bucket>` (Cloud Storage bucket for the logs).

- Gatekeeper reply text: Claude Haiku 4.5 on Vertex AI, region `us-east5`, mode `vertex`.
- Agents: Gemini 2.5 Pro on Vertex AI, region `us-central1`.
- Steps B-1 to B-6 must run in order. The 30 runs in B-5 are executed round-robin: P1' → P2A' → P2B' → P3B' → P3A'-LLM → P3A'-CANON is one round, repeated five times, so that time-of-day effects are spread across arms.
- Two terminals are used: **Terminal A = Gatekeeper**, **Terminal B = agents**. The study used two tabs of Google Cloud Shell (https://shell.cloud.google.com) opened on the project.

## B-1 Code and environment (Terminal A)

```bash
cd ~/ao_system_openclaw
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements-adversarial.txt pytest
mkdir -p ~/logs
pip freeze > ~/logs/pip_freeze.txt
python -c "import vertexai.generative_models; print('vertexai.generative_models OK')"
python -m pytest tests/ -q
```

The study reused the virtual environment of the May 2026 runs rather than reinstalling, so that a newer SDK could not change agent behaviour; its exact package versions are in `logs/rerun_2026-10/pip_freeze_2026-10.txt`.

Check: `vertexai.generative_models OK` is printed, and pytest ends with `17 passed` (14 before the retry-wrapper tests were added for the later runs). A deprecation warning from `vertexai.generative_models` can be ignored.

## B-2 Claude Haiku 4.5 connectivity and quota (Terminal A)

```bash
cd ~/ao_system_openclaw && source .venv/bin/activate
export AO_GCP_PROJECT_ID=<your-project>
export AO_GATEKEEPER_REGION=us-east5
export AO_GATEKEEPER_MODEL=claude-haiku-4-5
python test_claude_connection.py
```

Check: the final `=== Summary ===` block shows `ok: 10`, `429: 0`, `not_found: 0`, `other: 0`.

- `not_found`: enable Claude Haiku 4.5 for the project in the Vertex AI Model Garden, set `AO_GATEKEEPER_MODEL` to the dated model ID shown there, and run again.
- `429`: request a higher per-minute quota for `claude-haiku-4-5` in `us-east5` (IAM & Admin → Quotas). The pre-registered fallback, not needed in the study, was to run all 30 runs with `AO_GATEKEEPER_LLM_MODE=rules` (canned replies, no LLM) and say so; the two modes were never to be mixed.

## B-3 Environment variables (each terminal)

**Terminal A (Gatekeeper):**

```bash
cd ~/ao_system_openclaw && source .venv/bin/activate
export AO_GCP_PROJECT_ID=<your-project>
export AO_ADVERSARIAL_MODE=serve
export AO_GATEKEEPER_REGION=us-east5
export AO_GATEKEEPER_LLM_MODE=vertex
export AO_GATEKEEPER_MODEL=claude-haiku-4-5    # or the dated ID from B-2
export AO_SALES_AGENT_REGION=us-central1
```

`AO_GATEKEEPER_LLM_MODE` defaults to `hybrid`, which falls back to canned replies on HTTP 429; always set `vertex` explicitly.

**Terminal B (agents):**

```bash
cd ~/ao_system_openclaw/brain_cloud_openclaw/agents && source ~/ao_system_openclaw/.venv/bin/activate
export AO_GCP_PROJECT_ID=<your-project>
export AO_GCP_LOCATION=us-central1
export AO_GATEKEEPER_MODEL=claude-haiku-4-5    # same value as Terminal A
```

On the agent side `AO_GATEKEEPER_MODEL` is only a label written to the log (Terminal A decides the model actually used). If it is unset, the log records `"gatekeeper_model": "see mock log"`.

No `AO_PHASE1_*`, `AO_PHASE2_*` or `AO_PHASE3_*` variables may be left over in the shell (a new tab has none).

## B-4 Smoke test (not part of the study)

**Terminal A:**

```bash
export AO_GATEKEEPER_SCENARIO=phase2
python mock_adversarial_target.py 2>&1 | tee ~/logs/smoke_A.log
```

Wait until the `ADVERSARIAL_MOCK_SERVER_START` line shows `"gatekeeper_llm_mode": "vertex"` and the expected `"gatekeeper_model"`, and `Uvicorn running on http://0.0.0.0:8080` appears.

**Terminal B:**

```bash
python phase1_baseline_agent_openclaw.py 2>&1 | tee ~/logs/smoke_B.log
```

Checks:

- Terminal B: the first `GATEKEEPER_RESPONSE` has a `reply_text` without `Prompt:` or `Internal evaluation status` (no hidden-state leakage).
- Terminal B: `"gatekeeper_model"` shows the expected model in both the `STUDY_START` line (the label) and the `GATEKEEPER_RESPONSE` line (the model the mock used).
- Terminal B: `GEMINI_CALL_USAGE` lines carry numeric `prompt_tokens` (token accounting works).
- Terminal A: no `GATEKEEPER_RATE_LIMIT_RETRY` line (quota is sufficient).
- Terminal A: no `REPLY_EXTRACTION_FALLBACK` line. If one appears, that reply was replaced by a canned sentence; the run can continue, but record it.

If any check fails, stop and inspect both terminals before continuing. When the smoke test passes, stop the mock in Terminal A with Ctrl+C.

## B-5 The 30 runs

Restart the mock in Terminal A only when the scenario changes (phase2 ↔ phase3). Within a scenario no restart is needed: each run uses a new `transaction_id`, and the Gatekeeper keeps a separate thread per ID.

**Terminal A, Phase 1/2 arms:**

```bash
export AO_GATEKEEPER_SCENARIO=phase2
unset AO_GATEKEEPER_MAX_PITCH_CHARS
python mock_adversarial_target.py 2>&1 | tee -a ~/logs/mock_phase2.log
```

**Terminal A, Phase 3 arms:**

```bash
export AO_GATEKEEPER_SCENARIO=phase3 AO_GATEKEEPER_MAX_PITCH_CHARS=1000
python mock_adversarial_target.py 2>&1 | tee -a ~/logs/mock_phase3.log
```

When switching back from phase3 to phase2, `AO_GATEKEEPER_MAX_PITCH_CHARS` must be unset as above; the default is 300.

**Terminal B, the six arms** (`<n>` is the round number):

| Arm | Mock scenario | Command |
|---|---|---|
| P1' | phase2 | `python phase1_baseline_agent_openclaw.py 2>&1 \| tee ~/logs/P1_r<n>.log` |
| P2A' | phase2 | `AO_PHASE2_MONITOR_AI=off AO_PHASE2_TIER3_HARD_GATE=off python phase2_five_pillar_agent_openclaw.py 2>&1 \| tee ~/logs/P2A_r<n>.log` |
| P2B' | phase2 | `AO_PHASE2_MONITOR_AI=on AO_PHASE2_TIER3_HARD_GATE=on python phase2_five_pillar_agent_openclaw.py 2>&1 \| tee ~/logs/P2B_r<n>.log` |
| P3B' | phase3 | `AO_PHASE3_RUN=3B AO_PHASE3_ATOMIC_PURGE=off AO_PHASE3_RED_TEAM=off AO_PHASE3_MONITOR_AI=on AO_PHASE3_TIER3_HARD_GATE=on AO_PHASE3_MAX_OUTBOUND_CHARS=1000 python phase3_hybrid_agent_openclaw.py 2>&1 \| tee ~/logs/P3B_r<n>.log` |
| P3A'-LLM | phase3 | `AO_PHASE3_RUN=3A AO_PHASE3_ATOMIC_PURGE=on AO_PHASE3_RED_TEAM=on AO_PHASE3_RED_TEAM_CANONICAL=off AO_PHASE3_MONITOR_AI=on AO_PHASE3_TIER3_HARD_GATE=on AO_PHASE3_MAX_OUTBOUND_CHARS=1000 python phase3_hybrid_agent_openclaw.py 2>&1 \| tee ~/logs/P3A_LLM_r<n>.log` |
| P3A'-CANON | phase3 | `AO_PHASE3_RUN=3A AO_PHASE3_ATOMIC_PURGE=on AO_PHASE3_RED_TEAM=on AO_PHASE3_RED_TEAM_CANONICAL=on AO_PHASE3_MONITOR_AI=on AO_PHASE3_TIER3_HARD_GATE=on AO_PHASE3_MAX_OUTBOUND_CHARS=1000 python phase3_hybrid_agent_openclaw.py 2>&1 \| tee ~/logs/P3A_CANON_r<n>.log` |

Check at the start of each run (Terminal B), to catch a wrong arm:

- Phase 2: in `PHASE2_CONFIG`, `monitor_ai` / `tier3_hard_gate` are `false` / `false` for P2A' and `true` / `true` for P2B'.
- Phase 3: in `PHASE3_CONFIG`, `phase3_run` / `atomic_purge` / `red_team` / `red_team_canonical_first` are `3B` / `false` / `false` / `false` for P3B', `3A` / `true` / `true` / `false` for P3A'-LLM, and `3A` / `true` / `true` / `true` for P3A'-CANON.

End of a run: Terminal B prints a line with `"event": "STUDY_COMPLETE"`. Record its `transaction_id`, `outcome`, `turns_executed`, `total_gemini_api_calls` and `total_tokens`. Note any run with `fallback_pitch_used: true` or `director_plan_fallback: true` in Terminal B, or `REPLY_EXTRACTION_FALLBACK` in Terminal A (`grep -c '"fallback_pitch_used": true' ~/logs/<file>.log`). In P3A'-LLM, an LLM-written strike that fails the exception check is replaced by the canonical text, and the log then shows `fallback_pitch_used: true`.

If an HTTP call to the Gatekeeper fails in Phase 3 (`STUDY_ERROR`), the run ends without `STUDY_COMPLETE`. Such a run is invalid: repeat the same arm and record it.

After every run, copy the logs off the Cloud Shell machine:

```bash
gcloud storage cp ~/logs/*.log gs://<your-bucket>/rerun_2026-10/ --project=<your-project>
```

## B-6 Wrap-up

```bash
cd ~ && tar czf logs_paper2_rerun_2026-10.tgz logs
gcloud storage cp logs_paper2_rerun_2026-10.tgz gs://<your-bucket>/ --project=<your-project>
```

Claude Haiku 4.5 on Vertex AI is billed per request, so no resource needs to be stopped afterwards.

## Rules followed during the study

- The Gatekeeper's acceptance rules, the lexicon, the canonical strike text and the Monitor and Tier-3 logic were not changed.
- Invalid attempts were kept and are released with the valid runs (`logs/README.md`).
- Credentials and `.env` contents were never committed or logged.
