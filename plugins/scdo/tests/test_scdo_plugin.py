"""Offline tests: a fake scdo-agent CLI and a fake HTTP layer, so no keys, network or funds are used."""
import os
from pathlib import Path

import pytest

pytest.importorskip("game_sdk")
from scdo_plugin_gamesdk import ScdoAgent, ScdoWalletPlugin  # noqa: E402

FAKE = str(Path(__file__).with_name("fake_scdo_agent.py"))


def http(url, body=None, timeout=45):
    if "base.org" in url:
        return 200, {"result": hex(150000)}
    return 200, {"ok": True, "summary": {"balances": {"USDC": {"display": "0.150000"}}, "heartbeats": 1}}


def mk(tmp_path):
    return ScdoAgent(bin=FAKE, data_dir=str(tmp_path), http=http, env={"PATH": os.environ["PATH"]})


def test_functions_and_worker(tmp_path):
    p = ScdoWalletPlugin(bot="Game Bot", agent=mk(tmp_path))
    fns = {f.fn_name: f for f in p.get_functions()}
    assert set(fns) == {"scdo_register_agent", "scdo_create_wallet", "scdo_get_balance", "scdo_pay_x402", "scdo_book_income"}
    r = fns["scdo_register_agent"].execute(fn_id="1", args={})
    assert r.action_status.value == "done", r.feedback_message
    assert r.info["wallet"].startswith("0x")
    assert p.get_state()["scdo_wallet"] == r.info["wallet"]
    b = fns["scdo_get_balance"].execute(fn_id="2", args={})
    assert b.action_status.value == "done", b.feedback_message
    over_cap = fns["scdo_pay_x402"].execute(fn_id="3", args={"url": {"value": "https://x.example/p"}, "max_usdc": {"value": "5"}})
    assert over_cap.action_status.value == "failed"
    assert len(p.get_worker().action_space) == 5
