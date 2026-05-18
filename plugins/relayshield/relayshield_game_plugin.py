"""
RelayShield GAME Plugin
=======================
Identity threat intelligence for Virtuals Protocol GAME agents.

Wraps all RelayShield security tools as GAME-compatible Functions so any
GAME agent can check identity threats before acting on user input, executing
transactions, or processing links and files.

Tools:
  check_breach            — email breach lookup (HIBP, $0.10 USDC)
  check_sim_swap          — SIM swap / eSIM detection ($0.25 USDC)
  check_domain_lookalikes — typosquat / phishing domain scan ($0.50 USDC)
  check_oauth_watchlist   — breached OAuth app exposure ($0.15 USDC)
  scan_wallet             — on-chain wallet risk via GoPlus ($0.10 USDC)
  scan_url                — malware / phishing URL scan ($0.05 USDC)
  scan_file               — binary malware scan, 70+ AV engines ($0.10 USDC)
  check_scan_result       — poll async scan result (free)

Configuration (environment variables):
  RELAYSHIELD_API_URL   — API Gateway base URL (required)
                          https://xhh3tfrhng.execute-api.us-east-1.amazonaws.com/prod
  RELAYSHIELD_API_KEY   — RapidAPI subscription key (all tools, lower per-call cost)
  RELAYSHIELD_X_PAYMENT — x402 payment proof, USDC on Base (pay-as-you-go)

Payment:
  Pay-as-you-go via x402 on Base — set RELAYSHIELD_X_PAYMENT.
  Subscription via RapidAPI — set RELAYSHIELD_API_KEY.
  Free tier: https://rapidapi.com/relayshielduser/api/relayshield-security-intelligence

Usage:
  from relayshield_game_plugin import relayshield_functions
  worker = Worker(id="security_worker", functions=relayshield_functions, ...)
"""

import json
import os

import requests
from game_sdk.game.custom_types import Argument, Function, FunctionResultStatus

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

API_BASE = os.environ.get("RELAYSHIELD_API_URL", "").rstrip("/")
API_KEY = os.environ.get("RELAYSHIELD_API_KEY", "")
X_PAYMENT = os.environ.get("RELAYSHIELD_X_PAYMENT", "")

TIMEOUT = 30


def _headers() -> dict:
    h = {"Content-Type": "application/json"}
    if API_KEY:
        h["x-api-key"] = API_KEY
    elif X_PAYMENT:
        h["X-PAYMENT"] = X_PAYMENT
    return h


def _base() -> str:
    return f"{API_BASE}/v1/payg" if not API_KEY else f"{API_BASE}/v1"


def _call(method: str, path: str, body: dict | None = None) -> tuple[FunctionResultStatus, str, dict]:
    if not API_BASE:
        return (
            FunctionResultStatus.FAILED,
            "RELAYSHIELD_API_URL environment variable is not set.",
            {},
        )
    try:
        url = f"{_base()}{path}"
        resp = (
            requests.post(url, headers=_headers(), json=body, timeout=TIMEOUT)
            if method == "POST"
            else requests.get(url, headers=_headers(), timeout=TIMEOUT)
        )
        if resp.status_code == 402:
            return (
                FunctionResultStatus.FAILED,
                f"Payment required. Set RELAYSHIELD_X_PAYMENT (x402 USDC on Base) or "
                f"RELAYSHIELD_API_KEY (RapidAPI subscription). "
                f"Free tier: rapidapi.com/relayshielduser/api/relayshield-security-intelligence",
                {"status_code": 402},
            )
        data = resp.json()
        return FunctionResultStatus.DONE, json.dumps(data), data
    except requests.Timeout:
        return FunctionResultStatus.FAILED, "Request timed out after 30 seconds.", {}
    except Exception as exc:
        return FunctionResultStatus.FAILED, f"Request error: {exc}", {}


# ---------------------------------------------------------------------------
# Tool executables
# ---------------------------------------------------------------------------

def _check_breach(email: str) -> tuple[FunctionResultStatus, str, dict]:
    return _call("POST", "/breach", {"email": email})


def _check_sim_swap(phone: str) -> tuple[FunctionResultStatus, str, dict]:
    return _call("POST", "/sim-swap", {"phone": phone})


def _check_domain_lookalikes(domain: str) -> tuple[FunctionResultStatus, str, dict]:
    return _call("POST", "/domain", {"domain": domain})


def _check_oauth_watchlist(email: str) -> tuple[FunctionResultStatus, str, dict]:
    return _call("POST", "/oauth-watchlist", {"email": email})


def _scan_wallet(address: str, chain_id: str = "1") -> tuple[FunctionResultStatus, str, dict]:
    return _call("POST", "/scan-wallet", {"address": address, "chain_id": chain_id})


def _scan_url(url: str) -> tuple[FunctionResultStatus, str, dict]:
    return _call("POST", "/scan-url", {"url": url})


def _scan_file(file_url: str, filename: str = "") -> tuple[FunctionResultStatus, str, dict]:
    body: dict = {"file_url": file_url}
    if filename:
        body["filename"] = filename
    return _call("POST", "/scan-file", body)


def _check_scan_result(analysis_id: str) -> tuple[FunctionResultStatus, str, dict]:
    base = f"{API_BASE}/v1/payg" if not API_KEY else f"{API_BASE}/v1"
    if not API_BASE:
        return FunctionResultStatus.FAILED, "RELAYSHIELD_API_URL is not set.", {}
    try:
        resp = requests.get(
            f"{base}/result/{analysis_id}",
            headers=_headers(),
            timeout=TIMEOUT,
        )
        data = resp.json()
        return FunctionResultStatus.DONE, json.dumps(data), data
    except Exception as exc:
        return FunctionResultStatus.FAILED, f"Request error: {exc}", {}


# ---------------------------------------------------------------------------
# GAME Function definitions
# ---------------------------------------------------------------------------

relayshield_functions: list[Function] = [
    Function(
        fn_name="check_breach",
        fn_description=(
            "Check whether an email address appears in known data breaches. "
            "Uses Have I Been Pwned (13B+ compromised accounts). "
            "Call before high-risk actions that depend on credential integrity. "
            "Pay-as-you-go: $0.10 USDC on Base via x402."
        ),
        args=[
            Argument(
                name="email",
                description="Email address to check for breach exposure",
                type="string",
            )
        ],
        hint="Use before trusting a user's email-based credentials or identity claims.",
        executable=_check_breach,
    ),
    Function(
        fn_name="check_sim_swap",
        fn_description=(
            "Detect whether a SIM swap or eSIM provisioning event has occurred on a phone number "
            "in the last 24 hours. Uses live carrier data. "
            "Returns swapped (bool), timestamp, and current carrier. "
            "Call before completing actions that rely on SMS-based authentication. "
            "Pay-as-you-go: $0.25 USDC on Base via x402."
        ),
        args=[
            Argument(
                name="phone",
                description="Phone number in E.164 format (e.g. +14155551234)",
                type="string",
            )
        ],
        hint="Use when a user action depends on SMS 2FA or when a user reports losing mobile service.",
        executable=_check_sim_swap,
    ),
    Function(
        fn_name="check_domain_lookalikes",
        fn_description=(
            "Detect typosquat and lookalike domains impersonating a brand. "
            "Generates hundreds of permutations and resolves them via DNS. "
            "Enriches results with Certificate Transparency data. "
            "Returns all lookalike domains currently registered and resolving. "
            "Pay-as-you-go: $0.50 USDC on Base via x402."
        ),
        args=[
            Argument(
                name="domain",
                description="Root domain to scan for lookalikes (e.g. acme.com)",
                type="string",
            )
        ],
        hint="Use before a user clicks a link resembling a known brand domain.",
        executable=_check_domain_lookalikes,
    ),
    Function(
        fn_name="check_oauth_watchlist",
        fn_description=(
            "Check whether high-risk OAuth-connected SaaS apps (Slack, GitHub, Notion, Zapier, "
            "Vercel, HubSpot, AI tools, and more) linked to an email have appeared in recent breaches. "
            "A breached OAuth app may expose Google/Microsoft account access without touching the password. "
            "Pay-as-you-go: $0.15 USDC on Base via x402."
        ),
        args=[
            Argument(
                name="email",
                description="Email address whose connected OAuth apps to check",
                type="string",
            )
        ],
        hint="Use when evaluating identity trust for an email account before granting access.",
        executable=_check_oauth_watchlist,
    ),
    Function(
        fn_name="scan_wallet",
        fn_description=(
            "Check an EVM wallet address for on-chain risk signals using GoPlus Security. "
            "Detects blacklisted addresses, malicious activity, phishing associations, and contract risk. "
            "Returns risk_level (LOW/MEDIUM/HIGH) and risk_flags. "
            "Pay-as-you-go: $0.10 USDC on Base via x402."
        ),
        args=[
            Argument(
                name="address",
                description="EVM wallet address to scan (0x + 40 hex chars)",
                type="string",
            ),
            Argument(
                name="chain_id",
                description="EVM chain ID (default: 1 for Ethereum mainnet, 8453 for Base, 137 for Polygon)",
                type="string",
            ),
        ],
        hint="Use before sending funds to an unknown address or in DeFi due-diligence flows.",
        executable=_scan_wallet,
    ),
    Function(
        fn_name="scan_url",
        fn_description=(
            "Submit a URL for malware and phishing analysis across 70+ security engines. "
            "Returns an analysis_id immediately — call check_scan_result every 5 seconds until complete. "
            "Verdicts: malicious | suspicious | clean | timeout. "
            "Pay-as-you-go: $0.05 USDC on Base via x402."
        ),
        args=[
            Argument(
                name="url",
                description="URL to scan (must start with http:// or https://)",
                type="string",
            )
        ],
        hint="Use before navigating to an unfamiliar URL or when a user forwards a suspicious link.",
        executable=_scan_url,
    ),
    Function(
        fn_name="scan_file",
        fn_description=(
            "Submit a file for binary malware analysis across 70+ AV engines via a download URL. "
            "Returns an analysis_id immediately — call check_scan_result every 5 seconds until complete. "
            "Verdicts: malicious | suspicious | clean | timeout. "
            "Pay-as-you-go: $0.10 USDC on Base via x402."
        ),
        args=[
            Argument(
                name="file_url",
                description="Publicly accessible URL to download the file from",
                type="string",
            ),
            Argument(
                name="filename",
                description="Optional filename hint (e.g. invoice_march.pdf)",
                type="string",
            ),
        ],
        hint="Use when a user receives an email attachment and shares the download link.",
        executable=_scan_file,
    ),
    Function(
        fn_name="check_scan_result",
        fn_description=(
            "Poll for the result of a previously submitted URL or file scan. "
            "Call every 5 seconds after scan_url or scan_file until status is completed. "
            "Returns verdict (malicious/suspicious/clean) and engine vote counts. "
            "Free — no additional charge beyond the initial scan."
        ),
        args=[
            Argument(
                name="analysis_id",
                description="analysis_id returned by scan_url or scan_file",
                type="string",
            )
        ],
        hint="Always pair with scan_url or scan_file — poll until verdict is returned.",
        executable=_check_scan_result,
    ),
]
