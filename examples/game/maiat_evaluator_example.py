"""
Maiat Evaluator Example — Trust-based job evaluation for ACP agents.

This example shows how to use Maiat as your ACP evaluator to:
1. Auto-reject garbage deliverables (empty, "hello", "{}")
2. Auto-approve trusted providers (trust score >= 80)
3. Block low-trust providers (score < 30)
4. Record outcomes back to Maiat for trust score updates

Install:
    pip install maiat-evaluator acp-plugin-gamesdk

Usage:
    Set environment variables, then run this file.
"""

import os
from dotenv import load_dotenv

load_dotenv()

# ─── Option 1: One-liner with maiat-evaluator package ──────────────────────
# pip install maiat-evaluator

try:
    from maiat_evaluator import maiat_evaluator

    MAIAT_EVALUATOR = maiat_evaluator()  # default settings
    # Or with custom config:
    # MAIAT_EVALUATOR = maiat_evaluator(min_trust_score=50, auto_approve_trusted=False)
except ImportError:
    MAIAT_EVALUATOR = None
    print("maiat-evaluator not installed. Using inline evaluator below.")


# ─── Option 2: Inline evaluator (no extra dependency) ──────────────────────

import httpx

MAIAT_API_URL = os.getenv("MAIAT_API_URL", "https://app.maiat.io/api/v1")

GARBAGE_PATTERNS = {"hello", "hi", "test", "ok", "done", "yes", "no", "{}", "[]", "null"}


def maiat_evaluate_inline(job):
    """Inline Maiat evaluator — no extra package needed."""
    from virtuals_acp import ACPJobPhase

    for memo in job.memos:
        if memo.next_phase != ACPJobPhase.COMPLETED:
            continue

        deliverable = getattr(memo, "content", "") or ""
        provider = getattr(job, "provider_address", "") or ""

        # Step 1: Garbage check
        cleaned = deliverable.strip()
        if not cleaned or len(cleaned) < 20 or cleaned.lower() in GARBAGE_PATTERNS:
            print(f"[Maiat] Job {job.id}: REJECTED — garbage deliverable")
            job.evaluate(False)
            _record_outcome(provider, job.id, False, "garbage")
            return

        # Step 2: Trust score check
        score, verdict = _check_trust(provider)

        if verdict == "avoid" or score < 30:
            print(f"[Maiat] Job {job.id}: REJECTED — trust score {score}")
            job.evaluate(False)
            _record_outcome(provider, job.id, False, "low_trust")
            return

        # Step 3: Approve
        print(f"[Maiat] Job {job.id}: APPROVED — trust score {score}")
        job.evaluate(True)
        _record_outcome(provider, job.id, True, "approved")
        return


def _check_trust(address: str) -> tuple:
    """Query Maiat API for trust score."""
    try:
        resp = httpx.get(f"{MAIAT_API_URL}/evaluate", params={"address": address}, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        return data.get("trustScore", 0), data.get("verdict", "unknown")
    except Exception as e:
        print(f"[Maiat] Trust check failed: {e}")
        return 0, "unknown"


def _record_outcome(provider: str, job_id, approved: bool, reason: str):
    """Report outcome back to Maiat."""
    try:
        httpx.post(
            f"{MAIAT_API_URL}/outcome",
            json={
                "jobId": str(job_id),
                "provider": provider,
                "approved": approved,
                "reason": reason,
                "source": "game-sdk-example",
            },
            timeout=5,
        )
    except Exception:
        pass  # best effort


# ─── Agent Setup ────────────────────────────────────────────────────────────

def main():
    from acp_plugin_gamesdk import AcpPlugin, AcpPluginOptions
    from virtuals_acp import VirtualsACP

    # Pick evaluator: package version if installed, inline fallback
    on_evaluate = MAIAT_EVALUATOR if MAIAT_EVALUATOR else maiat_evaluate_inline

    acp_plugin = AcpPlugin(
        options=AcpPluginOptions(
            api_key=os.environ["GAME_API_KEY"],
            acp_client=VirtualsACP(
                wallet_private_key=os.environ["WALLET_PRIVATE_KEY"],
                agent_wallet_address=os.environ["AGENT_WALLET_ADDRESS"],
                entity_id=int(os.environ["ENTITY_ID"]),
                on_evaluate=on_evaluate,
            ),
            evaluator_cluster="MAIAT",
        )
    )

    print("[Maiat] Evaluator ready. Listening for jobs...")
    print(f"[Maiat] Using: {'maiat-evaluator package' if MAIAT_EVALUATOR else 'inline evaluator'}")

    # Your agent logic here...
    # The evaluator will automatically be called when jobs need evaluation.


if __name__ == "__main__":
    main()
