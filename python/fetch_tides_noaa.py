# fetch_tides_noaa.py — predictions + latest observed water level
import json, datetime as dt, configparser
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

def fetch_predictions(station, units="english", datum="MLLW"):
    today = dt.date.today()
    end = today + dt.timedelta(days=2)
    url = "https://api.tidesandcurrents.noaa.gov/api/prod/datagetter"
    params = {
        "begin_date": today.strftime("%Y%m%d"),
        "end_date": end.strftime("%Y%m%d"),
        "station": station,
        "product": "predictions",
        "datum": datum,
        "interval": "hilo",
        "time_zone": "lst_ldt",
        "units": units,
        "format": "json"
    }
    r = requests.get(url, params=params, timeout=15)
    r.raise_for_status()
    return r.json()

def fetch_water_level_latest(station, units="english", datum="MLLW", user_agent=None):
    url = "https://api.tidesandcurrents.noaa.gov/api/prod/datagetter"
    params = {
        "date": "latest",
        "station": station,
        "product": "water_level",
        "datum": datum,
        "time_zone": "lst_ldt",
        "units": units,
        "format": "json"
    }
    headers = {"User-Agent": user_agent} if user_agent else {}
    r = requests.get(url, params=params, headers=headers, timeout=15)
    r.raise_for_status()
    return r.json()

def simplify(pred_raw):
    preds = pred_raw.get("predictions", [])
    for p in preds:
        s = p.get("t")
        if s and " " in s:
            p["t"] = s.replace(" ", "T")
    return preds

def combine(pred_raw, wl_raw, units):
    out = {"predictions": simplify(pred_raw), "water_level": None}
    try:
        data = wl_raw.get("data", [])
        if data:
            rec = data[0]
            ts = rec.get("t")
            if ts and " " in ts:
                ts = ts.replace(" ", "T")
            val = rec.get("v")
            out["water_level"] = {
                "t": ts,
                "v": float(val) if val is not None else None,
                "unit": "ft" if units == "english" else "m"
            }
    except Exception:
        pass
    return out

def main():
    cfg = load_cfg()
    station = cfg.get("tides", "station", fallback="").strip()
    if not station:
        raise SystemExit("Set tides.station in python/config.ini")
    units = cfg.get("tides", "units", fallback="english")
    datum = cfg.get("tides", "datum", fallback="MLLW")
    user_agent = cfg.get("tides", "user_agent", fallback="dashboard-steph@bairey.com")

    pred_raw = fetch_predictions(station, units=units, datum=datum)
    wl_raw = fetch_water_level_latest(station, units=units, datum=datum, user_agent=user_agent)
    out = combine(pred_raw, wl_raw, units)

    DATA.mkdir(parents=True, exist_ok=True)
    (DATA / "tides.json").write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(f"Wrote {(DATA / 'tides.json')} with {len(out['predictions'])} predictions and water level present: {bool(out['water_level'])}")

if __name__ == "__main__":
    main()
