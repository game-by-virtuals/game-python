#!/usr/bin/env python3
"""Test double for the scdo-agent CLI. Writes only public files, never keys."""
import json, os, sys, time
a = sys.argv[1:]
def get(f):
    return a[a.index(f) + 1] if f in a else None
data = get("--data-dir")
open(os.path.join(data, "calls.log"), "a").write(json.dumps(a) + "\n")
cmd = a[4]
if cmd == "init":
    n = get("--name"); os.makedirs(os.path.join(data, n), exist_ok=True)
    json.dump({"address": "0x12522c713D49453f0FfD98A3D16Fca7aD4671960", "payout": get("--payout") or ""}, open(os.path.join(data, n, "meta.json"), "w"))
    print(f"Agent {n} is ready.")
elif cmd == "wallet" and a[5] == "create":
    n = get("--bot")
    json.dump({"botId": n, "address": "0x90306eF0Ab173FbfEf96E6CdE6fB591E0C8b1f8c", "network": "eip155:8453"}, open(os.path.join(data, n, "wallet.json"), "w"))
elif cmd == "pay":
    if "--dry-run" in a:
        print(f"Would pay {os.environ.get('FAKE_PRICE', '100000')} atomic units to 0x7f2F5DAB6B07b32b65286252bEd2d3c6C8081599.")
    else:
        print("Transaction: https://basescan.org/tx/0x" + "ab" * 32); print("Ledger: booked")
elif cmd == "run":
    time.sleep(30)
else:
    print("usage", file=sys.stderr); sys.exit(2)
