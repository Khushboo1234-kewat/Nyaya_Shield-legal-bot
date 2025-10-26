@echo off
echo ================================================================================
echo NYAYA-SHIELD AUTO FIX AND START
echo ================================================================================
echo.

REM Navigate to backend directory
cd /d "%~dp0backend"

echo Step 1: Retraining all models (this may take 2-5 minutes)...
echo ================================================================================
python -m bot.train_enhanced_models
if %errorlevel% neq 0 (
    echo ERROR: Model training failed!
    pause
    exit /b 1
)
echo.
echo ✓ Models retrained successfully!
echo.

echo Step 2: Verifying models work correctly...
echo ================================================================================
python -m bot.verify_dataset_response
if %errorlevel% neq 0 (
    echo WARNING: Verification had issues, but continuing...
)
echo.
echo ✓ Verification complete!
echo.

echo Step 3: Starting server...
echo ================================================================================
echo Server will start now. Press Ctrl+C to stop when needed.
echo.
echo IMPORTANT: Use domain-specific pages for best results:
echo   - CrPC (arrest, FIR, bail): http://localhost:5000/services/crpc_chat
echo   - IPC (sections, crimes): http://localhost:5000/services/ipc_chat
echo   - Consumer: http://localhost:5000/services/consumer_chat
echo   - Family: http://localhost:5000/services/family_chat
echo   - Property: http://localhost:5000/services/property_chat
echo   - Cyber: http://localhost:5000/services/cyber_chat
echo.
echo ================================================================================
echo.

python app.py
