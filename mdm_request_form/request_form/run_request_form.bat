@echo off
cd /d "%~dp0"
echo ============================================
echo   Lives Group MDM - Request Form prototype
echo ============================================
where python >nul 2>nul
if errorlevel 1 (
  where py >nul 2>nul
  if errorlevel 1 (
    echo Python was not found on this computer.
    echo Install it from https://www.python.org/downloads/ and tick "Add python.exe to PATH".
    pause
    exit /b 1
  )
  set PY=py
) else (
  set PY=python
)
echo Installing required packages (first run only, may take a minute)...
%PY% -m pip install --quiet -r requirements.txt
echo Starting the app - your browser will open at http://localhost:8501
%PY% -m streamlit run app.py --browser.gatherUsageStats false
pause
