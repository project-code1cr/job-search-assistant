@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
    py -m venv .venv || goto failed
)
".venv\Scripts\python.exe" -m pip install -r requirements.txt || goto failed
echo.
echo Open http://127.0.0.1:8000 in your browser. Keep this window open.
".venv\Scripts\python.exe" -m uvicorn app:app
if errorlevel 1 goto failed
exit /b 0

:failed
echo.
echo Setup or startup failed. Check the error above and see README.md.
pause
exit /b 1
