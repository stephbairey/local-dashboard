# fetch_calendar_ics.py — merge multiple Google ICS feeds into data\calendar.json
from __future__ import annotations
import json, datetime as dt, re
from pathlib import Path
from zoneinfo import ZoneInfo
import configparser, requests
from icalendar import Calendar as ICal
import recurring_ical_events as rie

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
CONF = ROOT / "data" / "config.ini"

LOCAL_TZ = ZoneInfo("America/Los_Angeles")
DAYS_AHEAD = 365
MAX_EVENTS = 120

def load_config():
    # Raw parser to avoid % interpolation errors in Google ICS URLs
    cp = configparser.RawConfigParser()
    cp.read(CONF, encoding="utf-8-sig")
    calmap = {}
    if cp.has_section("calendars_ics"):
        for name, url in cp["calendars_ics"].items():
            calmap[name] = url.strip()
    ua = "dashboard-local"
    if cp.has_section("weather_nws") and cp["weather_nws"].get("user_agent"):
        ua = cp["weather_nws"]["user_agent"].strip()
    return calmap, ua

def as_local_iso(dtobj: dt.datetime | None, all_day: bool) -> str | None:
    if not dtobj:
        return None
    if all_day:
        # all-day: local midnight, no timezone suffix
        d = dtobj.astimezone(LOCAL_TZ) if dtobj.tzinfo else dtobj.replace(tzinfo=LOCAL_TZ)
        return f"{d.year:04d}-{d.month:02d}-{d.day:02d}T00:00:00"
    d = dtobj.astimezone(LOCAL_TZ) if dtobj.tzinfo else dtobj.replace(tzinfo=LOCAL_TZ)
    return d.isoformat(timespec="seconds")

def to_utc(dtobj: dt.datetime | None, all_day: bool) -> dt.datetime | None:
    if not dtobj:
        return None
    d = dtobj
    if all_day and not d.tzinfo:
        d = d.replace(tzinfo=LOCAL_TZ)
    return d.astimezone(dt.timezone.utc)

def fetch_ics_text(name: str, url: str, headers: dict) -> str:
    r = requests.get(url, headers=headers, timeout=30)
    r.raise_for_status()
    return r.text

def event_times(ev) -> tuple[dt.datetime | None, dt.datetime | None, bool]:
    """
    Return (start_dt, end_dt, all_day)
    ev['DTSTART'].dt may be date or datetime. Same for DTEND.
    """
    def _get(field):
        v = ev.get(field)
        if v is None:
            return None
        d = v.dt
        # icalendar can give date or datetime
        if isinstance(d, dt.date) and not isinstance(d, dt.datetime):
            # midnight local for all-day handling
            return dt.datetime(d.year, d.month, d.day, 0, 0, 0, tzinfo=LOCAL_TZ)
        return d if isinstance(d, dt.datetime) else None

    start = _get("DTSTART")
    end   = _get("DTEND")
    # deduce all_day from DTSTART value type
    allday = False
    v = ev.get("DTSTART")
    if v is not None and isinstance(v.dt, dt.date) and not isinstance(v.dt, dt.datetime):
        allday = True
    # If DTEND missing on timed events, mirror start
    if start and not end:
        end = start
    return start, end, allday

def main():
    calendars, user_agent = load_config()
    if not calendars:
        raise SystemExit("No calendars in [calendars_ics] of python/config.ini")

    today = dt.datetime.now(LOCAL_TZ).date()
    window_start_local = dt.datetime(today.year, today.month, today.day, 0, 0, 0, tzinfo=LOCAL_TZ)
    window_end_local   = window_start_local + dt.timedelta(days=DAYS_AHEAD)
    window_start_utc   = window_start_local.astimezone(dt.timezone.utc)
    window_end_utc     = window_end_local.astimezone(dt.timezone.utc)

    headers = {"User-Agent": user_agent}
    merged: list[dict] = []

    for cal_name, url in calendars.items():
        try:
            txt = fetch_ics_text(cal_name, url, headers)
            ical = ICal.from_ical(txt)

            # Expand recurring events into individual instances within the window
            occs = rie.of(ical).between(window_start_local, window_end_local)
            count = 0

            for ev in occs:
                start, end, allday = event_times(ev)
                if not start:
                    continue

                # Filter by window in UTC
                s_utc = to_utc(start, allday)
                e_utc = to_utc(end,   allday) or s_utc
                if e_utc and e_utc < window_start_utc:
                    continue
                if s_utc and s_utc > window_end_utc:
                    continue

                title = (ev.get("SUMMARY") or "Untitled")
                if hasattr(title, "to_ical"):
                    try:
                        title = title.to_ical().decode("utf-8", "ignore")
                    except Exception:
                        title = str(title)

                loc = ev.get("LOCATION") or ""
                if hasattr(loc, "to_ical"):
                    try:
                        loc = loc.to_ical().decode("utf-8", "ignore")
                    except Exception:
                        loc = str(loc)
                if isinstance(loc, str) and loc.strip().lower() == "null":
                    loc = ""

                merged.append({
                    "title": str(title),
                    "start": as_local_iso(start, allday),
                    "end":   as_local_iso(end,   allday),
                    "location": str(loc),
                    "calendar": cal_name
                })
                count += 1

            print(f"- {cal_name}: parsed {count} instances")
        except Exception as e:
            print(f"[warn] {cal_name}: {e}")

    # Sort and trim
    def sortkey(ev):
        s = ev.get("start") or ""
        try:
            if re.search(r"(Z|[+-]\d{2}:\d{2})$", s):
                d = dt.datetime.fromisoformat(s.replace("Z", "+00:00"))
            else:
                d = dt.datetime.fromisoformat(s[:19])  # no tz -> local naive
                d = d.replace(tzinfo=LOCAL_TZ)
            return d.astimezone(dt.timezone.utc)
        except Exception:
            return dt.datetime.max.replace(tzinfo=dt.timezone.utc)

    merged = [m for m in merged if m.get("start")]
    merged.sort(key=sortkey)
    merged = merged[:MAX_EVENTS]

    DATA.mkdir(parents=True, exist_ok=True)
    out = {"events": merged}
    (DATA / "calendar.json").write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(f"Wrote {(DATA / 'calendar.json')} with {len(merged)} events from {len(calendars)} calendars.")

if __name__ == "__main__":
    main()
