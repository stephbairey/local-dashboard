#!/usr/bin/env python3
import json, time, urllib.request, urllib.parse, sys
from pathlib import Path
import configparser

ROOT = Path(__file__).resolve().parents[1]
CFG  = ROOT / "python" / "config.ini"
DATA = ROOT / "data" / "gc.json"
LOGF = ROOT / "data" / "dashboard.log"

def log(msg):
    try:
        from util.simplelog import append_line
        append_line(LOGF, f"[gc] {msg}")
    except Exception:
        pass

def read_cfg():
    cfg = configparser.ConfigParser(interpolation=None)
    cfg.read(CFG, encoding="utf-8")
    token   = cfg.get("gocardless", "access_token", fallback="").strip()
    sandbox = cfg.getboolean("gocardless", "sandbox", fallback=True)
    return token, sandbox

def get_json(base, path, token, params=None, timeout=25):
    q = ""
    if params:
        q = "?" + urllib.parse.urlencode(params)
    url = f"{base}{path}{q}"
    req = urllib.request.Request(url, headers={
        "Authorization": f"Bearer {token}",
        "GoCardless-Version": "2015-07-06",
        "Accept": "application/json",
        "User-Agent": "LocalDashboard/1.0 (+offline)"
    })
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))

def minor_to_units(amount, currency):
    # GoCardless uses minor units (e.g., cents). Safe string formatting.
    try:
        n = int(amount)
        return f"{n/100:.2f}", currency
    except Exception:
        return None, currency

def main():
    token, sandbox = read_cfg()
    if not token or "PASTE_YOUR_SANDBOX_ACCESS_TOKEN_HERE" in token:
        raise RuntimeError("Missing GoCardless access_token in python\\config.ini [gocardless]")

    base = "https://api-sandbox.gocardless.com" if sandbox else "https://api.gocardless.com"

    payouts  = get_json(base, "/payouts",  token, {"limit": 5})
    payments = get_json(base, "/payments", token, {"limit": 5})

    # Normalize a compact summary for the dashboard
    out = {
        "fetched_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "payouts": [],
        "payments": []
    }

    for p in payouts.get("payouts", []):
        amt, cur = minor_to_units(p.get("amount"), p.get("currency"))
        fees, _  = minor_to_units(p.get("deducted_fees"), p.get("currency"))
        out["payouts"].append({
            "id": p.get("id"),
            "status": p.get("status"),
            "currency": cur,
            "amount": amt,
            "deducted_fees": fees,
            "arrival_date": p.get("arrival_date"),
            "created_at": p.get("created_at")
        })

    for pm in payments.get("payments", []):
        amt, cur = minor_to_units(pm.get("amount"), pm.get("currency"))
        out["payments"].append({
            "id": pm.get("id"),
            "status": pm.get("status"),
            "currency": cur,
            "amount": amt,
            "description": pm.get("description"),
            "created_at": pm.get("created_at"),
            "charge_date": pm.get("charge_date")
        })

    DATA.parent.mkdir(parents=True, exist_ok=True)
    with open(DATA, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)

    log(f"OK payouts={len(out['payouts'])} payments={len(out['payments'])}")
    print("gc.json written")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        log(f"ERROR {e}")
        raise
