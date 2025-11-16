# Fetch weather using OpenWeather One Call. Writes data/weather.json
import os, json, time, configparser
from pathlib import Path

try:
    import requests
except ImportError:
    raise SystemExit("Please: pip install requests")

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
CFG = Path(__file__).resolve().parent / "config.ini"

def load_cfg():
    cp = configparser.ConfigParser()
    cp.read(CFG)
    return cp

def fetch(api_key, lat, lon, units="imperial"):
    url = "https://api.openweathermap.org/data/2.5/onecall"
    params = {
        "lat": lat, "lon": lon, "units": units,
        "exclude": "minutely,alerts", "appid": api_key
    }
    r = requests.get(url, params=params, timeout=15)
    r.raise_for_status()
    return r.json()

def simplify(raw):
    out = {
        "current": {
            "dt": raw.get("current", {}).get("dt"),
            "temp": raw.get("current", {}).get("temp"),
            "description": (raw.get("current", {}).get("weather") or [{}])[0].get("description", "")
        },
        "daily": [
            {
                "dt": d.get("dt"),
                "temp": {
                    "min": d.get("temp", {}).get("min"),
                    "max": d.get("temp", {}).get("max")
                }
            } for d in raw.get("daily", [])
        ]
    }
    return out

def main():
    cfg = load_cfg()
    api_key = cfg.get("weather", "api_key", fallback="").strip()
    lat = cfg.getfloat("weather", "lat", fallback=None)
    lon = cfg.getfloat("weather", "lon", fallback=None)
    units = cfg.get("weather", "units", fallback="imperial")

    if not api_key or lat is None or lon is None:
        raise SystemExit("Missing weather config in python/config.ini")

    raw = fetch(api_key, lat, lon, units=units)
    out = simplify(raw)
    DATA.mkdir(parents=True, exist_ok=True)
    (DATA / "weather.json").write_text(json.dumps(out, indent=2))

if __name__ == "__main__":
    main()
