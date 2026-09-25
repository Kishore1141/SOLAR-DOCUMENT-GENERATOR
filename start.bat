@echo off
REM Solar Documents Generator - start script (Windows)
cd /d %~dp0

if not exist venv (
    python -m venv venv
)
call venv\Scripts\activate.bat

pip install --quiet -r requirements.txt

echo.
echo Starting Solar Documents Generator...
echo Open http://localhost:5000 in your browser.
echo.
python server.py
pause
