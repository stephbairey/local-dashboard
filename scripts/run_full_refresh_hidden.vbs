Set oShell = CreateObject("WScript.Shell")
base = "C:\wamp64\www\dashboard"
py   = base & "\.venv\Scripts\pythonw.exe"

Sub RunIt(rel)
  cmd = """" & py & """" & " " & """" & base & "\python\run_fetch.py" & """" & " " & """" & base & "\python\" & rel & """"
  oShell.Run cmd, 0, False
End Sub

RunIt "fetch_weather_nws.py"
RunIt "fetch_tides_noaa.py"
RunIt "fetch_moon.py"
