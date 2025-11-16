' run_calendar_hidden.vbs — robust, self-logging
Option Explicit
Dim sh, logPath, py, runner, target, cmd
Set sh = CreateObject("WScript.Shell")

logPath = "C:\wamp64\www\dashboard\data\dashboard.log"
py      = """C:\Users\steph\AppData\Local\Programs\Python\Python312\python.exe"""
runner  = """C:\wamp64\www\dashboard\python\run_fetch.py"""
target  = """C:\wamp64\www\dashboard\python\fetch_calendar_ics.py"""

cmd = "cmd.exe /c (" _
    & "echo [CAL] %date% %time% start>>" & """" & logPath & """" & " & " _
    & py & " " & runner & " " & target & " >>" & """" & logPath & """" & " 2>&1 & " _
    & "echo [CAL] %date% %time% done>>" & """" & logPath & """" _
    & ")"

' 0 = hidden, True = wait until finished
sh.Run cmd, 0, True
