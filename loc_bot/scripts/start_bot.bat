@echo off
REM loc_bot 시작 스크립트
REM 콘솔 창이 열리며 봇이 실행됩니다. 창을 닫으면 봇이 종료됩니다.

cd /d "%~dp0.."
.venv\Scripts\python.exe -u -m src.main
pause
