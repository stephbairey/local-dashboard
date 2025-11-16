#!/usr/bin/env python3
import json, time, sys, urllib.request
from pathlib import Path
import configparser

ROOT = Path(__file__).resolve().parents[1]
CFG  = ROOT / "python" / "config.ini"
OUT  = ROOT / "data" / "bank.json"
LOGF = ROOT / "data" / "dashboard.log"

def log(msg):
    try:
        from util.simplelog import append_line
        append_line(LOGF, f"[plaid] {msg}")
    except Exception:
        pass

def plaid_base(env: str) -> str:
    e = (env or "sandbox").strip().lower()
    if e == "production": return "https://production.plaid.com"
    if e == "development": return "https://development.plaid.com"
    return "https://sandbox.plaid.com"

def http_post_json(url: str, body: dict) -> dict:
    req = urllib.request.Request(
        url,
        data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type":"application/json"},
        method="POST"
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        data = r.read().decode("utf-8")
        try:
            return json.loads(data)
        except Exception as e:
            raise RuntimeError(f"Bad JSON from Plaid: {e}: {data[:200]}")

def main():
    cfg = configparser.ConfigParser()
    cfg.read(CFG, encoding="utf-8")
    p = cfg["plaid"]

    env   = p.get("environment", "sandbox")
    cid   = p.get("client_id", "").strip()
    sec   = p.get("secret", "").strip()
    token = p.get("access_token", "").strip()

    if not (cid and sec and token):
        raise RuntimeError("Missing Plaid client_id, secret, or access_token in python\\config.ini [plaid]")

    base = plaid_base(env)

    # 1) Get account balances
    balances = http_post_json(f"{base}/accounts/balance/get", {
        "client_id": cid,
        "secret": sec,
        "access_token": token
    })

    accounts = balances.get("accounts", []) or []

    # Reduce to the fields we need
    acc_out = []
    totals = {}
    for a in accounts:
        b = a.get("balances", {}) or {}
        curr = float(b.get("current") or 0.0)
        avail = float(b.get("available") or 0.0)
        ccy = b.get("iso_currency_code") or b.get("unofficial_currency_code") or "USD"

        acc_out.append({
            "id": a.get("account_id"),
            "name": a.get("name") or a.get("official_name") or "Account",
            "mask": a.get("mask"),
            "type": a.get("type"),
            "subtype": a.get("subtype"),
            "current": curr,
            "available": avail,
            "currency": ccy
        })

        t = totals.setdefault(ccy, {"current":0.0, "available":0.0})
        t["current"] += curr
        t["available"] += avail

    out = {
        "fetched_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "accounts": acc_out,
        "totals": [{"currency": k, "current": round(v["current"],2), "available": round(v["available"],2)} for k,v in totals.items()]
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)

    log(f"OK accounts={len(acc_out)} totals=" + ",".join([f"{t['currency']}:{t['available']:.2f}" for t in out["totals"]]))
    print("bank.json written")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        log(f"ERROR {e}")
        raise
