@echo off
SETLOCAL ENABLEEXTENSIONS
SET SCRIPT_DIR=%~dp0
SET ROOT=%SCRIPT_DIR%..
SET PYW="%ROOT%\.venv\Scripts\pythonw.exe"

REM Full refresh (silent)
%PYW% "%ROOT%\python\fetch_weather_nws.py"
%PYW% "%ROOT%\python\fetch_tides_noaa.py"
%PYW% "%ROOT%\python\fetch_moon.py"
