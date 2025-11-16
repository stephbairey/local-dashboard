@echo off
SETLOCAL ENABLEEXTENSIONS
SET SCRIPT_DIR=%~dp0
SET ROOT=%SCRIPT_DIR%..
SET PYW="%ROOT%\.venv\Scripts\pythonw.exe"

REM Calendar-only (silent)
%PYW% "%ROOT%\python\fetch_calendar_all.py"
