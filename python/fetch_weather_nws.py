# fetch_weather_nws.py — latest obs (rich) + daily highs/lows via NWS points API
import json, time, configparser
import datetime as dt
from pathlib import Path

try:
    import requests
except ImportError:
    raise SystemExit("Please: pip install requests")

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
CFG = ROOT / "data" / "config.ini"

def load_cfg():
    cp = configparser.ConfigParser()
    cp.read(CFG, encoding="utf-8-sig")
    return cp

def headers(user_agent: str):
    return {
        "User-Agent": user_agent or "dashboard-steph@bairey.com",
        "Accept": "application/geo+json"
    }

def _iso_to_epoch(s: str) -> int:
    if s.endswith("Z"): s = s[:-1] + "+00:00"
    t = dt.datetime.fromisoformat(s)
    return int(t.timestamp())

# Unit helpers
def c_to_f(c): return (c * 9/5) + 32.0
def f_to_c(f): return (f - 32.0) * 5/9
def pa_to_inhg(pa): return pa / 3386.389
def pa_to_hpa(pa): return pa / 100.0
def ms_to_mph(ms): return ms * 2.236936
def ms_to_kmh(ms): return ms * 3.6
def m_to_mi(m): return m / 1609.344
def m_to_km(m): return m / 1000.0
def mm_to_in(mm): return mm / 25.4

def fetch_station_meta(station_id, h):
    url = f"https://api.weather.gov/stations/{station_id}"
    r = requests.get(url, headers=h, timeout=15); r.raise_for_status()
    j = r.json()
    coords = j.get("geometry", {}).get("coordinates", None)
    if not coords or len(coords) < 2:
        raise RuntimeError("Station metadata missing coordinates.")
    lon, lat = coords[0], coords[1]
    return float(lat), float(lon)

def fetch_latest_observation(station_id, h, units="imperial"):
    url = f"https://api.weather.gov/stations/{station_id}/observations/latest"
    r = requests.get(url, headers=h, params={"require_qc":"true"}, timeout=15); r.raise_for_status()
    p = r.json().get("properties", {}) or {}

    # Raw values (may be None)
    temp_c = (p.get("temperature") or {}).get("value")
    dew_c  = (p.get("dewpoint") or {}).get("value")
    rh_pct = (p.get("relativeHumidity") or {}).get("value")
    press_pa = (p.get("barometricPressure") or {}).get("value")
    wind_ms  = (p.get("windSpeed") or {}).get("value")
    gust_ms  = (p.get("windGust") or {}).get("value")
    wind_deg = (p.get("windDirection") or {}).get("value")
    vis_m    = (p.get("visibility") or {}).get("value")
    rain_mm1h = (p.get("precipitationLastHour") or {}).get("value")
    heat_c   = (p.get("heatIndex") or {}).get("value")
    chill_c  = (p.get("windChill") or {}).get("value")

    desc = p.get("textDescription") or "Weather"
    ts = p.get("timestamp")
    epoch = _iso_to_epoch(ts) if ts else int(time.time())

    # Convert to preferred units
    if units == "imperial":
        temp = None if temp_c is None else c_to_f(temp_c)
        dew  = None if dew_c  is None else c_to_f(dew_c)
        heat = None if heat_c is None else c_to_f(heat_c)
        chill= None if chill_c is None else c_to_f(chill_c)
        wind = None if wind_ms is None else ms_to_mph(wind_ms)
        gust = None if gust_ms is None else ms_to_mph(gust_ms)
        vis  = None if vis_m  is None else m_to_mi(vis_m)
        press_inhg = None if press_pa is None else pa_to_inhg(press_pa)
        press_hpa  = None if press_pa is None else pa_to_hpa(press_pa)
        rain_in = None if rain_mm1h is None else mm_to_in(rain_mm1h)
    else:  # metric
        temp = temp_c
        dew  = dew_c
        heat = heat_c
        chill= chill_c
        wind = None if wind_ms is None else ms_to_kmh(wind_ms)
        gust = None if gust_ms is None else ms_to_kmh(gust_ms)
        vis  = None if vis_m  is None else m_to_km(vis_m)
        press_inhg = None
        press_hpa  = None if press_pa is None else pa_to_hpa(press_pa)
        rain_in = None  # we’ll keep mm via extras

    current = {
        "dt": epoch,
        "temp": None if temp is None else round(temp, 1),
        "description": desc,
        "humidity": None if rh_pct is None else round(rh_pct, 0),
        "pressure_inHg": None if press_inhg is None else round(press_inhg, 2),
        "pressure_hPa": None if press_hpa is None else round(press_hpa, 0),
        "wind_mph": None if wind is None else round(wind, 1),
        "wind_gust_mph": None if gust is None else round(gust, 1),
        "wind_deg": None if wind_deg is None else int(wind_deg),
        "dewpoint_f": None if dew is None else round(dew, 1),
        "visibility_mi": None if vis is None else round(vis, 1),
        "precip_1h_in": None if rain_in is None else round(rain_in, 2),
        "heat_index_f": None if heat is None else round(heat, 1),
        "wind_chill_f": None if chill is None else round(chill, 1),
        "station": station_id
    }

    # For metric consumers, you could also pack an "extras_metric" block. Keeping simple for now.
    return current

def fetch_forecast_daily(lat, lon, h, units="imperial"):
    # Collapse NWS 12h periods into per-day hi/lo for the next 5 days
    pt = requests.get(f"https://api.weather.gov/points/{lat},{lon}", headers=h, timeout=15)
    pt.raise_for_status()
    fc_url = pt.json().get("properties", {}).get("forecast")
    if not fc_url: raise RuntimeError("No forecast URL found for point.")
    r2 = requests.get(fc_url, headers=h, timeout=15); r2.raise_for_status()
    periods = r2.json().get("properties", {}).get("periods", []) or []

    def convert_temp(val, unit):
        if val is None: return None
        if units == "imperial" and unit.upper() == "C": return c_to_f(val)
        if units == "metric" and unit.upper() == "F":  return f_to_c(val)
        return float(val)

    days = {}
    first_desc = None
    for p in periods:
        st = p.get("startTime")
        if not st: continue
        date_key = st[:10]
        t = p.get("temperature"); unit = (p.get("temperatureUnit") or "F").upper()
        t = convert_temp(t, unit)
        if t is None: continue
        rec = days.setdefault(date_key, {"min": None, "max": None})
        rec["min"] = t if rec["min"] is None else min(rec["min"], t)
        rec["max"] = t if rec["max"] is None else max(rec["max"], t)
        if first_desc is None:
            first_desc = p.get("shortForecast") or p.get("detailedForecast") or "Forecast"

    out_daily, today = [], dt.date.today()
    for i in range(0, 5):
        d = today + dt.timedelta(days=i)
        key = d.isoformat()
        rec = days.get(key)
        if not rec: continue
        noon = dt.datetime(d.year, d.month, d.day, 12, 0, 0)
        out_daily.append({
            "dt": int(noon.timestamp()),
            "temp": {
                "min": None if rec["min"] is None else round(rec["min"]),
                "max": None if rec["max"] is None else round(rec["max"])
            }
        })
    return first_desc, out_daily

def main():
    cfg = load_cfg()
    station = cfg.get("weather_nws", "station", fallback="KPDX").strip()
    ua = cfg.get("weather_nws", "user_agent", fallback="dashboard-steph@bairey.com")
    units = cfg.get("weather_nws", "units", fallback="imperial")

    h = headers(ua)
    current = fetch_latest_observation(station, h, units=units)
    lat, lon = fetch_station_meta(station, h)
    desc, daily = fetch_forecast_daily(lat, lon, h, units=units)

    if (not current.get("description")) and desc:
        current["description"] = desc

    DATA.mkdir(parents=True, exist_ok=True)
    out = {"current": current, "daily": daily}
    (DATA / "weather.json").write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(f'Wrote {(DATA / "weather.json")} with current temp={current.get("temp")} and {len(daily)} daily entries.')

if __name__ == "__main__":
    main()
