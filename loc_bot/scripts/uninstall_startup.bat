@echo off
REM Windows 시작프로그램에서 loc_bot을 제거합니다.

set SHORTCUT_PATH=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\loc_bot.lnk

if exist "%SHORTCUT_PATH%" (
    del "%SHORTCUT_PATH%"
    echo [OK] loc_bot이 시작프로그램에서 제거되었습니다.
) else (
    echo [INFO] loc_bot이 시작프로그램에 등록되어 있지 않습니다.
)
pause
