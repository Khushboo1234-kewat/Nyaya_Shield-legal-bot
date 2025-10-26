@echo off
setlocal enabledelayedexpansion

echo ===== Starting Application =====
echo Date: %DATE%
echo Time: %TIME%
echo Current Directory: %CD%
echo.

echo === Python Information ===
python --version
echo.

echo === Environment Variables ===
set | findstr /i "python"
echo.

echo === Running Application ===
python -c "import sys; print('Python Path:', sys.executable); print('Version:', sys.version)"
echo.

python run_app.py

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo === ERROR: Application failed to start ===
    exit /b 1
)

pause
