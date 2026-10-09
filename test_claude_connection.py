# test_claude_connection.py
# -*- coding: utf-8 -*-

import os
import time

from anthropic import AnthropicVertex, NotFoundError, RateLimitError

NUM_CALLS = 10


def classify_error(exc: Exception) -> str:
    message = str(exc).lower()
    if isinstance(exc, RateLimitError) or "429" in message or "resource_exhausted" in message:
        return "429"
    if isinstance(exc, NotFoundError) or "not_found" in message or "404" in message:
        return "not_found"
    return "other"


def check_claude_gatekeeper():
    # Same client settings as mock_adversarial_target.py (Gatekeeper side)
    PROJECT_ID = os.environ.get("AO_GCP_PROJECT_ID", "openclaw-sandbox-env")
    REGION = os.environ.get("AO_GATEKEEPER_REGION", "us-east5")
    # If the alias returns NOT_FOUND, pass the dated Model Garden ID (claude-haiku-4-5@YYYYMMDD)
    MODEL_ID = os.environ.get("AO_GATEKEEPER_MODEL", "claude-haiku-4-5")

    print(f"Initializing AnthropicVertex (Project: {PROJECT_ID}, Region: {REGION})...")
    client = AnthropicVertex(project_id=PROJECT_ID, region=REGION, max_retries=0)
    print(f"Model: {MODEL_ID} — sending {NUM_CALLS} consecutive calls (max_tokens=50)")

    counts = {"ok": 0, "429": 0, "not_found": 0, "other": 0}
    for i in range(1, NUM_CALLS + 1):
        started = time.monotonic()
        try:
            response = client.messages.create(
                model=MODEL_ID,
                max_tokens=50,
                messages=[{"role": "user", "content": "Reply with one short sentence."}],
            )
            elapsed = time.monotonic() - started
            counts["ok"] += 1
            print(
                f"[{i:02d}] OK {elapsed:.2f}s model={response.model} "
                f"usage=(input_tokens={response.usage.input_tokens}, "
                f"output_tokens={response.usage.output_tokens})"
            )
        except Exception as e:
            elapsed = time.monotonic() - started
            kind = classify_error(e)
            counts[kind] += 1
            print(f"[{i:02d}] ERROR({kind}) {elapsed:.2f}s {type(e).__name__}: {e}")

    print("\n=== Summary ===")
    for kind, count in counts.items():
        print(f"{kind}: {count}")
    return counts


if __name__ == "__main__":
    result = check_claude_gatekeeper()
    raise SystemExit(0 if result["ok"] == NUM_CALLS else 1)
