#!/usr/bin/env python3
import json, time, urllib.request
from pathlib import Path
import configparser

ROOT = Path(__file__).resolve().parents[1]
CFG  = ROOT / "python" / "config.ini"
DATA = ROOT / "data" / "bank.json"
LOGF = ROOT / "data" / "dashboard.log"

def log(msg):
    try:
        from util.simplelog import append_line
        append_line(LOGF, f"[plaid] {msg}")
    except Exception:
        pass

def post_json(url, payload):
    req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type":"application/json"}, method="POST")
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode("utf-8"))

def main():
    cfg = configparser.ConfigParser(interpolation=None)
    cfg.read(CFG, encoding="utf-8")
    env   = (cfg.get("plaid","environment", fallback="development") or "development").strip().lower()
    cid   = cfg.get("plaid","client_id", fallback="").strip()
    sec   = cfg.get("plaid","secret", fallback="").strip()
    token = cfg.get("plaid","access_token", fallback="").strip()
    if not (cid and sec and token):
        raise SystemExit("Missing plaid client_id/secret/access_token in python\\config.ini")

    base = "https://sandbox.plaid.com" if env=="sandbox" else "https://development.plaid.com"
    j = post_json(f"{base}/accounts/balance/get", {"client_id":cid,"secret":sec,"access_token":token})
    accounts = j.get("accounts", [])

    # Summarize balances
    out = {
        "fetched_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "accounts": [{
            "name": a.get("name"),
            "official_name": a.get("official_name"),
            "mask": a.get("mask"),
            "type": a.get("type"),
            "subtype": a.get("subtype"),
            "balances": {
                "available": a.get("balances",{}).get("available"),
                "current":   a.get("balances",{}).get("current"),
                "iso_currency_code": a.get("balances",{}).get("iso_currency_code")
            }
        } for a in accounts]
    }

    DATA.parent.mkdir(parents=True, exist_ok=True)
    with open(DATA, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)

    log(f"OK accounts={len(accounts)}")
    print("bank.json written")

if __name__ == "__main__":
    main()
