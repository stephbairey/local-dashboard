# fetch_calendar_google.py
import json, datetime as dt
from pathlib import Path

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
CREDS_FILE = Path(__file__).resolve().parent / "credentials.json"
TOKEN_FILE = Path(__file__).resolve().parent / "token.json"

SCOPES = ["https://www.googleapis.com/auth/calendar.readonly"]

def get_creds():
    creds = None
    if TOKEN_FILE.exists():
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(str(CREDS_FILE), SCOPES)
            creds = flow.run_local_server(port=0, access_type="offline", prompt="consent")
        TOKEN_FILE.write_text(creds.to_json())
    return creds

def to_iso(start_obj):
    # Google returns either dateTime or date (all-day)
    if "dateTime" in start_obj:
        return start_obj["dateTime"]
    # For all-day, make it local midnight so JS treats it as local time
    return start_obj["date"] + "T00:00:00"

def main():
    creds = get_creds()
    service = build("calendar", "v3", credentials=creds)

    # Pull from now forward
    now = dt.datetime.utcnow().isoformat() + "Z"
    # Get events from primary. If you want all visible calendars later, we can list them and merge.
    result = service.events().list(
        calendarId="primary",
        timeMin=now,
        maxResults=20,
        singleEvents=True,
        orderBy="startTime"
    ).execute()

    items = result.get("items", [])
    events = []
    for e in items:
        start = e.get("start", {})
        end = e.get("end", {})
        events.append({
            "title": e.get("summary", "Untitled"),
            "start": to_iso(start),
            "end": to_iso(end) if end else None,
            "location": e.get("location", "")
        })

    DATA.mkdir(parents=True, exist_ok=True)
    (DATA / "calendar.json").write_text(json.dumps({"events": events}, indent=2), encoding="utf-8")
    print(f"Wrote {(DATA / 'calendar.json')} with {len(events)} events.")

if __name__ == "__main__":
    try:
        main()
    except HttpError as err:
        print(f"Google API error: {err}")
