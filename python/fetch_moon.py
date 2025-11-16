# fetch_moon.py — local moon phase, illumination, and upcoming quarter dates
import json, math, datetime as dt
from pathlib import Path
from zoneinfo import ZoneInfo
from astral import moon

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
LOCAL_TZ = ZoneInfo("America/Los_Angeles")
SYNODIC = 29.530588853  # days

def phase_name(age: float) -> str:
    if age < 0.5 or age > SYNODIC - 0.5: return "New Moon"
    if age < 6.5:  return "Waxing Crescent"
    if age < 8.5:  return "First Quarter"
    if age < 13.0: return "Waxing Gibbous"
    if age < 16.0: return "Full Moon"
    if age < 21.0: return "Waning Gibbous"
    if age < 23.5: return "Last Quarter"
    return "Waning Crescent"

def next_phase_iso(today: dt.date, target_age: float) -> str:
    curr = float(moon.phase(today))
    delta_days = (target_age - curr) % SYNODIC
    d = today + dt.timedelta(days=delta_days)
    noon = dt.datetime(d.year, d.month, d.day, 12, 0, tzinfo=LOCAL_TZ)
    return noon.isoformat()

def main():
    now = dt.datetime.now(LOCAL_TZ)
    today = now.date()
    age = float(moon.phase(today))
    illum = 0.5 * (1 - math.cos(2 * math.pi * (age / SYNODIC)))  # 0..1

    out = {
        "current": {
            "dt": int(now.timestamp()),
            "age_days": round(age, 2),
            "phase_name": phase_name(age),
            "illumination_pct": round(illum * 100, 1)
        },
        "next": {
            "new_moon":      next_phase_iso(today, 0.0),
            "first_quarter": next_phase_iso(today, SYNODIC * 0.25),
            "full_moon":     next_phase_iso(today, SYNODIC * 0.50),
            "last_quarter":  next_phase_iso(today, SYNODIC * 0.75)
        }
    }

    DATA.mkdir(parents=True, exist_ok=True)
    (DATA / "moon.json").write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(f"Wrote {(DATA / 'moon.json')} with phase {out['current']['phase_name']} ({out['current']['illumination_pct']}%).")

if __name__ == "__main__":
    main()
