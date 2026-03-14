@echo off
REM Windows 시작프로그램에 loc_bot을 등록합니다.
REM 실행하면 PC 부팅 시 자동으로 봇이 백그라운드에서 시작됩니다.

set STARTUP_FOLDER=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup
set VBS_PATH=%~dp0start_bot_silent.vbs
set SHORTCUT_PATH=%STARTUP_FOLDER%\loc_bot.lnk

REM 바로가기 생성
powershell -Command "$ws = New-Object -ComObject WScript.Shell; $s = $ws.CreateShortcut('%SHORTCUT_PATH%'); $s.TargetPath = 'wscript.exe'; $s.Arguments = '\"%VBS_PATH%\"'; $s.WorkingDirectory = '%~dp0..'; $s.Description = 'loc_bot Telegram Bot'; $s.Save()"

if exist "%SHORTCUT_PATH%" (
    echo [OK] loc_bot이 시작프로그램에 등록되었습니다.
    echo      경로: %SHORTCUT_PATH%
    echo      PC를 재시작하면 자동으로 봇이 실행됩니다.
) else (
    echo [ERROR] 등록에 실패했습니다.
)
pause
