#!/usr/bin/env python3
import json, time, urllib.request, configparser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CFG  = ROOT / "python" / "config.ini"
DATA = ROOT / "data" / "sun.json"

def log(msg):
    try:
        from util.simplelog import append_line
        append_line(ROOT / "data" / "dashboard.log", f"[sun] {msg}")
    except Exception:
        pass

def strip_seconds_clock(s):
    # "6:49:03 AM" -> "6:49 AM"  or pass through "6:49 AM"
    import re
    m = re.match(r"^(\d{1,2}:\d{2})(?::\d{2})?\s*([AP]M)$", str(s or "").strip(), re.I)
    return f"{m.group(1)} {m.group(2).upper()}" if m else (s or "")

def main():
    cfg = configparser.ConfigParser()
    cfg.read(CFG, encoding="utf-8")
    lat = cfg.getfloat("weather", "lat", fallback=45.582)
    lon = cfg.getfloat("weather", "lon", fallback=-122.675)

    url = f"https://api.sunrisesunset.io/json?lat={lat}&lng={lon}"
    req = urllib.request.Request(url, headers={"User-Agent":"LocalDashboard/1.0"})
    with urllib.request.urlopen(req, timeout=20) as r:
        data = json.loads(r.read().decode("utf-8"))

    res = data.get("results", {}) or {}
    out = {
        "date": res.get("date"),
        "timezone": res.get("timezone"),
        "sunrise": strip_seconds_clock(res.get("sunrise")),
        "sunset":  strip_seconds_clock(res.get("sunset")),
        "first_light": res.get("first_light"),
        "last_light":  res.get("last_light"),
        "dawn": res.get("dawn"),
        "dusk": res.get("dusk"),
        "solar_noon": res.get("solar_noon"),
        "day_length": res.get("day_length"),
        "fetched_at": time.strftime("%Y-%m-%dT%H:%M:%S")
    }

    DATA.parent.mkdir(parents=True, exist_ok=True)
    with open(DATA, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)

    log(f"OK sunrise {out.get('sunrise')} sunset {out.get('sunset')}")
    print("sun.json written")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        log(f"ERROR {e}")
        raise
