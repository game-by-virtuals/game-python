"""SCDO agent core: a thin wrapper around the scdo-agent CLI and the public Agent Ledger API.

Keys never leave the agent's data dir. This module never reads key files and never prints secrets.
"""
from __future__ import annotations

import base64
import datetime as _dt
import json
import os
import re
import shutil
import subprocess
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Optional

DOCS_URL = "https://scdo.com.au/linux-agent/"
LEDGER_URL = "https://scdo.com.au/agent-ledger/api"
RELAY_URL = "https://scdo.com.au/x402-base/"
FEED_URL = "https://scdo.com.au/downloads/wallet/linux/latest.json"

NETWORKS = {
    "base": {"id": "eip155:8453", "label": "Base mainnet", "usdc": "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913", "rpc": "https://mainnet.base.org"},
    "base-sepolia": {"id": "eip155:84532", "label": "Base Sepolia (test network)", "usdc": "0x036CbD53842c5426634e7929541eC2318f3dCF7e", "rpc": "https://sepolia.base.org"},
}

# Same caps as the SCDO x402 relay.
MIN_ATOMIC = 1_000
MAX_ATOMIC = 1_000_000
DAILY_COUNT = 100
DAILY_ATOMIC = 20_000_000
CAPS_TEXT = "0.001 to 1 USDC per payment, 100 payments and 20 USDC per day"

_ADDR = re.compile(r"^0x[0-9a-fA-F]{40}$")
_NAME = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,63}$")
_TX = re.compile(r"0x[0-9a-fA-F]{64}")


class ScdoError(Exception):
    def __init__(self, code: str, message: str):
        super().__init__(f"{code}: {message}")
        self.code = code


def parse_network(value: Optional[str]) -> str:
    v = (value or "base").strip().lower()
    if v in ("", "base", "mainnet", "eip155:8453"):
        return "base"
    if v in ("base-sepolia", "testnet", "sepolia", "eip155:84532"):
        return "base-sepolia"
    raise ScdoError("network", f'network must be "base" (mainnet) or "base-sepolia" (testnet), got {value}')


def usdc_to_atomic(value: Any) -> int:
    s = str(value).strip()
    if not re.fullmatch(r"\d+(\.\d{1,6})?", s):
        raise ScdoError("amount", f"not a USDC amount: {value}")
    w, _, f = s.partition(".")
    return int(w) * 1_000_000 + int((f + "000000")[:6])


def atomic_to_usdc(atomic: int) -> str:
    a = int(atomic)
    return f"{a // 1_000_000}.{a % 1_000_000:06d}"


def check_amount(atomic: int) -> int:
    a = int(atomic)
    if a < MIN_ATOMIC or a > MAX_ATOMIC:
        raise ScdoError("cap", f"amount {atomic_to_usdc(a)} USDC is outside the 0.001 to 1 USDC per-settlement cap")
    return a


def _name(n: Any, field: str = "bot") -> str:
    if not isinstance(n, str) or not _NAME.match(n):
        raise ScdoError("name", f"{field} must match {_NAME.pattern}")
    return n


def default_data_dir(env=os.environ) -> str:
    if env.get("SCDO_AGENT_DATA", "").strip():
        return env["SCDO_AGENT_DATA"].strip()
    user = Path(env.get("HOME") or Path.home()) / ".local" / "share" / "scdo-agent"
    if user.exists() or not Path("/var/lib/scdo-agent").exists():
        return str(user)
    return "/var/lib/scdo-agent"


def find_bin(env=os.environ) -> Optional[str]:
    if env.get("SCDO_AGENT_BIN", "").strip():
        return env["SCDO_AGENT_BIN"].strip()
    found = shutil.which("scdo-agent", path=env.get("PATH"))
    if found:
        return found
    for d in (Path(env.get("HOME") or Path.home()) / ".scdo-agent" / "bin", Path(env.get("HOME") or Path.home()) / ".local" / "bin", Path("/usr/local/bin"), Path("/usr/bin")):
        if (d / "scdo-agent").exists():
            return str(d / "scdo-agent")
    return None


def install_bin(env=os.environ) -> str:
    """Download the scdo-agent CLI (Linux amd64/arm64) from the SCDO feed into ~/.scdo-agent/bin, sha256-checked.
    Lets a framework plugin work after a single pip install. Set SCDO_AGENT_NO_DOWNLOAD=1 to disable."""
    import hashlib, io, platform, tarfile
    if platform.system() != "Linux":
        raise ScdoError("no_cli", f"scdo-agent auto-install is Linux only. Install it first: {DOCS_URL}")
    arch = {"x86_64": "amd64", "amd64": "amd64", "aarch64": "arm64", "arm64": "arm64"}.get(platform.machine().lower())
    if not arch:
        raise ScdoError("no_cli", f"unsupported CPU {platform.machine()} (amd64, arm64)")
    ua = {"user-agent": "scdo-agent-tools"}
    with urllib.request.urlopen(urllib.request.Request(env.get("SCDO_FEED") or FEED_URL, headers=ua), timeout=60) as r:
        feed = json.load(r)
    f = (feed.get("files") or {}).get(arch) or (feed if arch == "amd64" else None)
    if not f or not str(f.get("url", "")).startswith("https://scdo.com.au/") or not re.match(r"^[0-9a-f]{64}$", f.get("sha256", "")):
        raise ScdoError("no_cli", "bad SCDO feed")
    with urllib.request.urlopen(urllib.request.Request(f["url"], headers=ua), timeout=300) as r:
        buf = r.read()
    if hashlib.sha256(buf).hexdigest() != f["sha256"]:
        raise ScdoError("no_cli", "scdo-agent sha256 mismatch")
    with tarfile.open(fileobj=io.BytesIO(buf)) as t:
        m = t.extractfile("scdo-agent")
        data = m.read()
    d = Path(env.get("HOME") or Path.home()) / ".scdo-agent" / "bin"
    d.mkdir(parents=True, exist_ok=True, mode=0o700)
    out = d / "scdo-agent"; tmp = d / "scdo-agent.tmp"
    tmp.write_bytes(data); tmp.chmod(0o755); os.replace(tmp, out)
    return str(out)


def scrub(text: str) -> str:
    return re.sub(r"(private[_ ]?key|mnemonic|seed|passphrase)\s*[:=]\s*\S+", r"\1: [redacted]", text or "", flags=re.I)


def decode_payment(s: Any) -> dict:
    if isinstance(s, dict):
        return s
    t = str(s).strip()
    if t.startswith("{"):
        return json.loads(t)
    return json.loads(base64.b64decode(t).decode())


def _http_json(url: str, body: Optional[dict] = None, timeout: float = 45) -> tuple[int, dict]:
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, headers={"content-type": "application/json", "accept": "application/json", "user-agent": "scdo-agent-tools"}, method="POST" if data else "GET")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, json.loads(r.read() or b"{}")
    except urllib.error.HTTPError as e:
        try:
            return e.code, json.loads(e.read() or b"{}")
        except ValueError:
            return e.code, {}
    except (urllib.error.URLError, TimeoutError) as e:
        return 0, {"error": str(e)}


class ScdoAgent:
    """Per-agent SCDO x402 wallet. Defaults to Base mainnet; pass network="base-sepolia" for the test network."""

    def __init__(self, bin: Optional[str] = None, data_dir: Optional[str] = None, network: Optional[str] = None,
                 ledger_url: Optional[str] = None, passphrase_file: Optional[str] = None,
                 http: Optional[Callable[..., tuple[int, dict]]] = None, env=None, timeout: float = 180):
        self.env = dict(env if env is not None else os.environ)
        self.bin = bin or find_bin(self.env)
        self.data_dir = data_dir or default_data_dir(self.env)
        self.network = parse_network(network or self.env.get("SCDO_AGENT_NETWORK") or "base")
        self.ledger_url = (ledger_url or self.env.get("SCDO_AGENT_LEDGER") or LEDGER_URL).rstrip("/")
        self.passphrase_file = passphrase_file or self.env.get("SCDO_AGENT_PASSPHRASE_FILE", "")
        self.http = http or _http_json
        self.timeout = timeout

    # ---- plumbing ----
    def _require_bin(self) -> str:
        if (not self.bin or not Path(self.bin).exists()) and self.env.get("SCDO_AGENT_NO_DOWNLOAD") != "1":
            self.bin = install_bin(self.env)
        if not self.bin or not Path(self.bin).exists():
            raise ScdoError("no_cli", f"scdo-agent is not installed. Install it first: {DOCS_URL}")
        return self.bin

    def _env(self) -> dict:
        e = {**self.env, "LANG": "C.UTF-8", "LC_ALL": "C.UTF-8"}
        if self.passphrase_file:
            e["SCDO_AGENT_PASSPHRASE_FILE"] = self.passphrase_file
        return e

    def run(self, args: list[str]) -> tuple[int, str, str]:
        cmd = [self._require_bin(), "--lang", "en", "--data-dir", self.data_dir, *args]
        try:
            p = subprocess.run(cmd, env=self._env(), capture_output=True, text=True, timeout=self.timeout)
        except subprocess.TimeoutExpired:
            return 1, "", "timeout"
        return p.returncode, scrub(p.stdout), scrub(p.stderr)

    def agent_dir(self, name: str) -> Path:
        return Path(self.data_dir) / _name(name)

    def _read(self, name: str, file: str) -> Optional[dict]:
        p = self.agent_dir(name) / file
        return json.loads(p.read_text()) if p.exists() else None

    def meta(self, name: str) -> Optional[dict]:
        m = self._read(name, "meta.json")
        if not m:
            return None
        return {"name": name, "address": m.get("address"), "payout": m.get("payout") or None, "role": m.get("role")}

    def wallet_doc(self, name: str) -> Optional[dict]:
        w = self._read(name, "wallet.json")
        if not w:
            return None
        return {"bot": w.get("botId") or name, "address": w.get("address"), "network": w.get("network"), "killed": bool(w.get("killed"))}

    # ---- tools ----
    def register_agent(self, name: str, payout: Optional[str] = None, label: Optional[str] = None, heartbeats: bool = True) -> dict:
        _name(name, "name")
        if payout and not _ADDR.match(payout):
            raise ScdoError("payout", "payout must be a 0x address")
        created = False
        if not self.meta(name):
            args = ["init", "--name", name]
            if payout:
                args += ["--payout", payout]
            if label:
                args += ["--label", str(label)[:80]]
            code, out, err = self.run(args)
            if code != 0:
                raise ScdoError("init", (err or out).strip())
            created = True
        meta = self.meta(name)
        hb = self.start_heartbeats(name) if heartbeats else "off"
        return {"name": name, "agent": meta["address"], "payout": meta["payout"], "role": "bookkeeping node", "dataDir": self.data_dir,
                "created": created, "heartbeats": hb, "ledger": f"{self.ledger_url}/agents/{meta['address']}"}

    def start_heartbeats(self, name: str) -> str:
        bin_ = self._require_bin()
        d = self.agent_dir(name)
        d.mkdir(parents=True, exist_ok=True)
        log_path = d / "plugin-run.log"
        with open(log_path, "a") as log:
            p = subprocess.Popen([bin_, "--lang", "en", "--data-dir", self.data_dir, "run", "--name", name], env=self._env(),
                                 stdin=subprocess.DEVNULL, stdout=log, stderr=log, start_new_session=True)
        try:
            code = p.wait(timeout=3)
        except subprocess.TimeoutExpired:
            return "started"
        tail = "\n".join(log_path.read_text().splitlines()[-5:])
        if re.search(r"already running", tail, re.I):
            return "running"
        raise ScdoError("heartbeat", scrub(tail.strip()) or f"scdo-agent run exited {code}")

    def create_wallet(self, bot: str, network: Optional[str] = None, max_usdc: str = "0.10", daily_usdc: str = "1.00") -> dict:
        _name(bot)
        net = parse_network(network or self.network)
        mx = check_amount(usdc_to_atomic(max_usdc))
        daily = usdc_to_atomic(daily_usdc)
        if daily < mx or daily > DAILY_ATOMIC:
            raise ScdoError("cap", "daily_usdc must be at least max_usdc and at most 20 USDC")
        if not self.meta(bot):
            raise ScdoError("not_registered", f"agent {bot} does not exist yet; call register_agent first")
        code, out, err = self.run(["wallet", "create", "--bot", bot, "--network", net, "--asset", "usdc", "--max", atomic_to_usdc(mx), "--daily", atomic_to_usdc(daily)])
        if code != 0:
            raise ScdoError("wallet", (err or out).strip())
        doc = self.wallet_doc(bot) or {}
        n = NETWORKS[net]
        return {"bot": bot, "agent": self.meta(bot)["address"], "wallet": doc.get("address"), "network": n["id"], "networkLabel": n["label"],
                "maxUsdc": atomic_to_usdc(mx), "dailyUsdc": atomic_to_usdc(daily),
                "fundWith": f"Send USDC on {n['label']} to {doc.get('address')}. No ETH is needed; the facilitator pays gas."}

    def get_balance(self, bot: str, network: Optional[str] = None) -> dict:
        _name(bot)
        net = parse_network(network or self.network)
        meta = self.meta(bot)
        if not meta:
            raise ScdoError("not_registered", f"agent {bot} not found in {self.data_dir}")
        doc = self.wallet_doc(bot)
        onchain = None
        if doc and doc.get("address"):
            data = "0x70a08231" + doc["address"][2:].lower().rjust(64, "0")
            st, j = self.http(NETWORKS[net]["rpc"], {"jsonrpc": "2.0", "id": 1, "method": "eth_call", "params": [{"to": NETWORKS[net]["usdc"], "data": data}, "latest"]})
            if j.get("result"):
                a = int(j["result"], 16)
                onchain = {"atomic": str(a), "usdc": atomic_to_usdc(a)}
        st, s = self.http(f"{self.ledger_url}/agents/{meta['address']}")
        if st == 200 and s.get("ok"):
            sm = s.get("summary", {})
            b = sm.get("balances", {})
            ledger = {"usdc": b.get("USDC", {}).get("display"), "testUsdc": b.get("tUSDC", {}).get("display"), "scdo": b.get("WSCDO", {}).get("display"),
                      "usdcWallet": sm.get("usdcWallet"), "online": sm.get("online"), "heartbeats": sm.get("heartbeats")}
        else:
            ledger = {"error": f"ledger {st}: {s.get('error', 'error')}"}
        return {"bot": bot, "agent": meta["address"], "wallet": doc.get("address") if doc else None, "network": NETWORKS[net]["id"], "onchainUsdc": onchain, "ledger": ledger}

    def _caps_path(self, bot: str) -> Path:
        return self.agent_dir(bot) / "plugin-caps.json"

    def read_caps(self, bot: str) -> dict:
        day = _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%d")
        try:
            c = json.loads(self._caps_path(bot).read_text())
            if c.get("day") == day:
                return {"day": day, "count": int(c.get("count", 0)), "atomic": int(c.get("atomic", "0"))}
        except (OSError, ValueError):
            pass
        return {"day": day, "count": 0, "atomic": 0}

    def write_caps(self, bot: str, c: dict) -> None:
        p = self._caps_path(bot)
        tmp = p.with_suffix(".tmp")
        tmp.write_text(json.dumps({"day": c["day"], "count": c["count"], "atomic": str(c["atomic"])}))
        tmp.replace(p)

    def pay_x402(self, bot: str, url: str, max_usdc: str = "0.10", network: Optional[str] = None) -> dict:
        _name(bot)
        if not re.match(r"^https?://", str(url or "")):
            raise ScdoError("url", "url must be an http(s) URL")
        net = parse_network(network or self.network)
        mx = check_amount(usdc_to_atomic(max_usdc))
        caps = self.read_caps(bot)
        if caps["count"] >= DAILY_COUNT:
            raise ScdoError("cap", "daily cap reached: 100 payments today")
        code, out, err = self.run(["pay", url, "--bot", bot, "--network", net, "--max", atomic_to_usdc(mx), "--dry-run"])
        m = re.search(r"Would pay (\d+) atomic units to (0x[0-9a-fA-F]{40})", out)
        if code != 0 or not m:
            raise ScdoError("preview", (err or out).strip() or "price preview failed")
        amount = check_amount(int(m.group(1)))
        if amount > mx:
            raise ScdoError("cap", f"price {atomic_to_usdc(amount)} USDC is above max_usdc {atomic_to_usdc(mx)}")
        if caps["atomic"] + amount > DAILY_ATOMIC:
            raise ScdoError("cap", "daily cap reached: 20 USDC today")
        code, out, err = self.run(["pay", url, "--bot", bot, "--network", net, "--max", atomic_to_usdc(amount)])
        tl = re.search(r"Transaction: (\S+)", out)
        tx = (_TX.search(tl.group(1)) or [None])[0] if tl else None
        if tx:
            caps["count"] += 1
            caps["atomic"] += amount
            self.write_caps(bot, caps)
        if code != 0 and not tx:
            raise ScdoError("limit" if code == 3 else "pay", (err or out).strip())
        lg = re.search(r"Ledger: (.+)", out)
        explorer = (f"https://basescan.org/tx/{tx}" if net == "base" else f"https://sepolia.basescan.org/tx/{tx}") if tx else None
        return {"bot": bot, "url": url, "network": NETWORKS[net]["id"], "amountUsdc": atomic_to_usdc(amount), "payTo": m.group(2), "tx": tx,
                "explorer": explorer, "ledger": lg.group(1).strip() if lg else None, "ok": code == 0,
                "capsToday": {"payments": caps["count"], "usdc": atomic_to_usdc(caps["atomic"])}}

    def book_income(self, payment_payload: Any, settlement: Any, agent: Optional[str] = None, bot: Optional[str] = None,
                    payment_requirements: Optional[dict] = None) -> dict:
        addr = agent
        if not addr and bot:
            addr = (self.meta(_name(bot)) or {}).get("address")
        if not addr or not _ADDR.match(addr):
            raise ScdoError("agent", "agent (0x address) or a local bot name is required")
        payload = decode_payment(payment_payload)
        reqs = payment_requirements or payload.get("accepted")
        if not reqs:
            raise ScdoError("payload", "payment_requirements is required")
        amount = reqs.get("amount") or reqs.get("maxAmountRequired") or ((payload.get("payload") or {}).get("authorization") or {}).get("value")
        if amount is not None:
            check_amount(int(amount))
        tx = settlement if isinstance(settlement, str) else (settlement or {}).get("transaction")
        if not tx or not re.fullmatch(r"0x[0-9a-fA-F]{64}", tx):
            raise ScdoError("settlement", "settlement transaction hash is required")
        s_obj = settlement if isinstance(settlement, dict) else {}
        body = {"agent": addr, "x402Version": payload.get("x402Version") or 2, "paymentPayload": payload, "paymentRequirements": reqs,
                "settlement": {"success": True, "transaction": tx, "network": s_obj.get("network") or reqs.get("network"),
                               "payer": s_obj.get("payer") or ((payload.get("payload") or {}).get("authorization") or {}).get("from")}}
        st, j = 0, {}
        for i in range(6):
            st, j = self.http(f"{self.ledger_url}/ledger/income", body)
            if st == 200 and j.get("ok"):
                e = j.get("entry") or {}
                return {"ok": True, "agent": addr, "duplicate": bool(j.get("duplicate")),
                        "entry": {k: e.get(k) for k in ("id", "kind", "amount", "asset", "tx", "confirmed")}}
            if not (j.get("error") == "settlementPending" or st in (0, 502, 503, 504)):
                break
            time.sleep((i + 1) * 2)
        raise ScdoError("ledger", f"ledger {st}: {j.get('error', 'error')}")
