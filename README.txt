Home Dashboard Starter

Install
1) Copy the 'dashboard_starter' contents to C:\wamp64\www\dashboard
   The final structure should be C:\wamp64\www\dashboard\index.php and the assets, api, slides, data, python, scripts folders.

2) In C:\wamp64\www\dashboard\python copy config.example.ini to config.ini and fill values.

   - For weather, create an OpenWeather key, then set lat and lon.
   - For calendar, export an ICS file for now and point to it. Later you can swap in the Google Calendar API.
   - For tides, set your NOAA station id.

3) Test in a browser at http://localhost/dashboard/
   You should see sample data immediately. JS rotates slides every 18 seconds.

4) Install Python packages in a venv or system Python:
   pip install requests icalendar

5) Run the fetchers once:
   C:\wamp64\www\dashboard\scripts\run_all_fetchers.bat

6) Windows Task Scheduler. Create a Basic Task that runs the .bat every 15 minutes.
   Program to start: C:\Windows\System32\cmd.exe
   Arguments: /c "C:\wamp64\www\dashboard\scripts\run_all_fetchers.bat"

Notes
- The frontend requests JSON through /dashboard/api/read.php which serves files from /dashboard/data with no cache.
- You can add new slides by duplicating a <section class="slide"> in index.php and creating a new JSON file plus a renderer in assets/js/app.js.
- CSS is minimal. Tweak fonts and layout to fit your display.
