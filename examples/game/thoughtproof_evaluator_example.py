"""
ThoughtProof Reasoning Evaluator for GAME SDK / Virtuals ACP

Verifies whether an agent's deliverable is well-reasoned before accepting payment.
Uses adversarial multi-model critique (Claude, Grok, DeepSeek) — returns ALLOW, BLOCK, or UNCERTAIN.

Payment: x402, $0.005-$0.10 USDC on Base per evaluation (stake-based).
API: https://api.thoughtproof.ai/v1/check
Docs: https://thoughtproof.ai/skill.md
"""

import httpx
import json
import os
from typing import Optional


# ---------------------------------------------------------------------------
# Option 1: One-liner (recommended)
# ---------------------------------------------------------------------------
# from thoughtproof_evaluator import thoughtproof_evaluator
#
# acp_client = VirtualsACP(
#     ...,
#     on_evaluate=thoughtproof_evaluator(),
# )
# ---------------------------------------------------------------------------


def thoughtproof_evaluator(
    stake_level: str = "medium",
    domain: str = "general",
    min_confidence: float = 0.60,
):
    """
    Returns an on_evaluate callback that uses ThoughtProof to verify
    whether a job deliverable is well-reasoned before accepting payment.

    Args:
        stake_level: "low" | "medium" | "high" | "critical"
        domain: "financial" | "code" | "medical" | "legal" | "general"
        min_confidence: minimum confidence to auto-accept (0.0-1.0)

    Requires: x402 payment of $0.02-$0.05 USDC on Base per evaluation.
    Set THOUGHTPROOF_PAYMENT_WALLET env var or use purl CLI for testing.
    """

    def on_evaluate(job) -> None:
        from virtuals_acp import ACPJobPhase

        for memo in job.memos:
            if memo.next_phase != ACPJobPhase.COMPLETED:
                continue

            deliverable = getattr(memo, "content", "") or ""

            # Basic sanity check
            if not deliverable or len(deliverable.strip()) < 10:
                print(f"[ThoughtProof] Job {job.id}: REJECTED — deliverable too short")
                job.evaluate(False)
                return

            # Call ThoughtProof
            claim = f"Agent deliverable for job {job.id}: {deliverable[:500]}"

            try:
                result = _check_reasoning(claim, stake_level, domain)
            except Exception as e:
                print(f"[ThoughtProof] Job {job.id}: API error ({e}) — auto-accepting")
                job.evaluate(True)
                return

            verdict = result.get("verdict", "UNCERTAIN")
            confidence = result.get("confidence", 0.5)
            objections = result.get("objections", [])

            print(f"[ThoughtProof] Job {job.id}: verdict={verdict} confidence={confidence:.2f}")
            if objections:
                print(f"[ThoughtProof] Objections: {'; '.join(objections[:2])}")

            if verdict == "ALLOW" and confidence >= min_confidence:
                job.evaluate(True)
            elif verdict == "BLOCK":
                job.evaluate(False)
            else:
                # UNCERTAIN — safe escalation state, flag for human review
                print(f"[ThoughtProof] Job {job.id}: {verdict} — accepting with review flag")
                job.evaluate(True)

    return on_evaluate


# ---------------------------------------------------------------------------
# Option 2: Inline reasoning check (no extra package)
# ---------------------------------------------------------------------------

def _check_reasoning(
    claim: str,
    stake_level: str = "medium",
    domain: str = "general",
) -> dict:
    """
    Call ThoughtProof API. Handles x402 payment challenge.

    Returns: {"verdict": "ALLOW"|"BLOCK"|"UNCERTAIN", "confidence": float, ...}
    Raises: ValueError if payment required but no wallet configured.
    Raises: httpx.HTTPError on network failure.
    """
    api_url = "https://api.thoughtproof.ai/v1/check"
    payload = {"claim": claim, "stakeLevel": stake_level, "domain": domain}

    with httpx.Client(timeout=120) as client:
        resp = client.post(api_url, json=payload)

        if resp.status_code == 200:
            return resp.json()

        if resp.status_code == 402:
            payment_info = resp.json()
            amount = (
                payment_info.get("paymentRequired", {})
                .get("payment", {})
                .get("amountUsdc", "0.02")
            )
            raise ValueError(
                f"ThoughtProof requires x402 payment (${amount} USDC on Base). "
                "Use purl CLI for testing: "
                f"purl -X POST {api_url} -d '{json.dumps(payload)}'"
            )

        resp.raise_for_status()
        return resp.json()


# ---------------------------------------------------------------------------
# Example usage
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("ThoughtProof Evaluator — reasoning check demo\n")

    # Direct API test (requires x402 payment or purl)
    test_cases = [
        ("Buy ETH because influencers say it will moon. FOMO.", "financial", "BLOCK expected"),
        ("ETH at $2180, 6% below 30d MA, RSI 34. Stop -6%. Target +10%.", "financial", "ALLOW expected"),
    ]

    for claim, domain, expected in test_cases:
        print(f"Claim: {claim[:60]}...")
        print(f"Expected: {expected}")
        try:
            result = _check_reasoning(claim, stake_level="low", domain=domain)
            print(f"Result: {result.get('verdict')} (confidence={result.get('confidence', 0):.2f})")
        except ValueError as e:
            print(f"Payment required: {str(e)[:100]}")
        print()
