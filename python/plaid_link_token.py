#!/usr/bin/env python3
import json, time, os, ssl, urllib.request, urllib.error, configparser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CFG  = ROOT / "python" / "config.ini"
OUT  = ROOT / "data"  / "plaid_link_token.json"

def post_json(url, payload):
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers={
        "Content-Type":"application/json",
        "Accept":"application/json"
    })
    ctx = ssl.create_default_context()
    try:
        with urllib.request.urlopen(req, timeout=30, context=ctx) as resp:
            return resp.getcode(), json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8","replace") if e.fp else ""
        try: body_json = json.loads(body)
        except Exception: body_json = {"non_json_body": body}
        return e.code, {"_http_error": True, "status": e.code, "reason": e.reason, "body": body_json}
    except Exception as e:
        return None, {"_exception": True, "error": str(e)}

def read_cfg():
    cfg = configparser.ConfigParser(interpolation=None)
    cfg.read(CFG, encoding="utf-8")
    if not cfg.has_section("plaid"):
        raise SystemExit("No [plaid] section found in python/config.ini")
    P = cfg["plaid"]
    return {
        "client_id": P.get("client_id","").strip(),
        "secret": P.get("secret","").strip(),
        "environment": P.get("environment","sandbox").strip().lower(),
        "redirect_uri": P.get("redirect_uri","").strip(),
        "products": [x.strip() for x in P.get("products","transactions").split(",") if x.strip()],
        "country_codes": [x.strip().upper() for x in P.get("country_codes","US").split(",") if x.strip()],
        "hosted_link": P.get("hosted_link","false").strip().lower() in ("1","true","yes","on")
    }

def main():
    C = read_cfg()
    if not C["client_id"] or not C["secret"]:
        raise SystemExit("Missing [plaid] client_id or secret")
    host = "sandbox.plaid.com" if C["environment"].startswith("sand") else "production.plaid.com"

    payload = {
        "client_id": C["client_id"],
        "secret": C["secret"],
        "client_name": "Local Dashboard",
        "language": "en",
        "country_codes": C["country_codes"],
        "user": {"client_user_id": os.environ.get("USERNAME","local-user")},
        "products": C["products"]
    }
    # Prefer Hosted Link if you set hosted_link = true in config.ini
    if C["hosted_link"]:
        payload["hosted_link"] = {}
    elif C["redirect_uri"]:
        payload["redirect_uri"] = C["redirect_uri"]

    debug = {
        "env": C["environment"], "host": host,
        "has_client_id": bool(C["client_id"]), "secret_len": len(C["secret"]),
        "hosted_link": C["hosted_link"], "redirect_uri": bool(C["redirect_uri"]),
        "products": C["products"], "countries": C["country_codes"]
    }
    print("DEBUG:", json.dumps(debug, indent=2))

    status, body = post_json(f"https://{host}/link/token/create", payload)
    print("HTTP_STATUS:", status)
    print("RESPONSE:", json.dumps(body, indent=2))

    ok = isinstance(body, dict) and ("link_token" in body)
    if ok:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        with open(OUT, "w", encoding="utf-8") as f:
            json.dump({
                "env": C["environment"], "host": host, "ok": True,
                "link_token": body.get("link_token"),
                "hosted_link_url": body.get("hosted_link_url"),
                "expiration": body.get("expiration"),
                "raw": body, "fetched_at": time.strftime("%Y-%m-%dT%H:%M:%S")
            }, f, ensure_ascii=False, indent=2)
        print("Wrote", OUT)
    else:
        print("Did not write token file.")

if __name__ == "__main__":
    main()
