@echo off
SETLOCAL ENABLEEXTENSIONS
SET SCRIPT_DIR=%~dp0
SET ROOT=%SCRIPT_DIR%..
SET PY="%ROOT%\.venv\Scripts\python.exe"

echo Using Python at %PY%
%PY% --version

REM Fetchers
%PY% "%ROOT%\python\fetch_weather_nws.py"
%PY% "%ROOT%\python\fetch_calendar_all.py"
%PY% "%ROOT%\python\fetch_tides_noaa.py"

echo Done.
