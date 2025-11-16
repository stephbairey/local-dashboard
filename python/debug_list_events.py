# debug_list_events.py — counts upcoming events per calendar (next 90 days)
import datetime as dt
from pathlib import Path

from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request

ROOT = Path(__file__).resolve().parents[1]
TOKEN_FILE = Path(__file__).resolve().parent / "token.json"
SCOPES = ["https://www.googleapis.com/auth/calendar.readonly"]

def get_creds():
    if not TOKEN_FILE.exists():
        raise SystemExit("No token.json yet. Run fetch_calendar_google.py once to create it.")
    creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
    if not creds.valid and creds.refresh_token:
        creds.refresh(Request()); TOKEN_FILE.write_text(creds.to_json())
    return creds

def main():
    svc = build("calendar", "v3", credentials=get_creds())
    now = dt.datetime.now(dt.timezone.utc)
    time_min = now.isoformat().replace("+00:00", "Z")
    time_max = (now + dt.timedelta(days=90)).isoformat().replace("+00:00", "Z")

    print("Scanning calendars for events in the next 90 days:\n")
    page = None
    while True:
        resp = svc.calendarList().list(pageToken=page).execute()
        for c in resp.get("items", []):
            cal_id = c.get("id"); name = c.get("summary"); role = c.get("accessRole")
            total = 0; sample = []
            p2 = None
            while True:
                r2 = svc.events().list(
                    calendarId=cal_id, timeMin=time_min, timeMax=time_max,
                    singleEvents=True, orderBy="startTime", maxResults=250, pageToken=p2
                ).execute()
                items = r2.get("items", [])
                total += len(items)
                for e in items[:3]:
                    s = e.get("start", {}).get("dateTime") or (e.get("start", {}).get("date") + "T00:00:00")
                    sample.append(f"  - {s}  {e.get('summary','Untitled')}")
                p2 = r2.get("nextPageToken")
                if not p2: break
            print(f"- {name}  (role:{role})  events:{total}")
            for line in sample:
                print(line)
            if total == 0:
                print("  (no events in window)")
            print()
        page = resp.get("nextPageToken")
        if not page: break

if __name__ == "__main__":
    main()
