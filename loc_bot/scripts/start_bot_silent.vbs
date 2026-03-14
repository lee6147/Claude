' loc_bot 백그라운드 시작 스크립트
' 콘솔 창 없이 봇을 실행합니다.
' 종료하려면 작업 관리자에서 python.exe를 종료하세요.

Set WshShell = CreateObject("WScript.Shell")
WshShell.CurrentDirectory = CreateObject("Scripting.FileSystemObject").GetParentFolderName(WScript.ScriptFullName) & "\.."
WshShell.Run """.venv\Scripts\pythonw.exe"" -u -m src.main", 0, False
