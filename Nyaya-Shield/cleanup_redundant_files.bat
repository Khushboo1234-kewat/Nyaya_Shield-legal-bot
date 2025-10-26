@echo off
REM ========================================
REM Nyaya-Shield Project Cleanup Script
REM Removes duplicate and unnecessary files
REM ========================================

echo.
echo ========================================
echo Nyaya-Shield Project Cleanup
echo ========================================
echo.

REM Navigate to project root
cd /d "%~dp0"

echo [1/4] Removing redundant .md documentation files...
del /F /Q "AUTO_FIX_README.md" 2>nul
del /F /Q "CRITICAL_FIX_NEEDED.md" 2>nul
del /F /Q "ENHANCED_RESPONSES_ALL_DOMAINS.md" 2>nul
del /F /Q "ENHANCED_TRAINING_GUIDE.md" 2>nul
del /F /Q "ENSURE_DATASET_ANSWERS.md" 2>nul
del /F /Q "ENSURE_SPECIFIC_REPLIES.md" 2>nul
del /F /Q "FEATURE_COMPLETE.md" 2>nul
del /F /Q "FINAL_FIX_APPLIED.md" 2>nul
del /F /Q "FIXES_APPLIED.md" 2>nul
del /F /Q "FIX_GUIDE.md" 2>nul
del /F /Q "FIX_NOW.md" 2>nul
del /F /Q "IMPLEMENTATION_SUMMARY.md" 2>nul
del /F /Q "MULTI_DATASET_SEARCH.md" 2>nul
del /F /Q "QUICK_START.md" 2>nul
del /F /Q "QUICK_TEST_GUIDE.md" 2>nul
del /F /Q "READY_TO_TRAIN.md" 2>nul
del /F /Q "TEST_QUESTIONS.md" 2>nul
del /F /Q "USER_FRIENDLY_RESPONSES.md" 2>nul
del /F /Q "VERIFICATION_REPORT.md" 2>nul
del /F /Q "YOUR_BOT_IS_READY.md" 2>nul
echo   ✓ Removed 20 redundant .md files

echo.
echo [2/4] Removing duplicate backend venv directory...
if exist "backend\venv" (
    rmdir /S /Q "backend\venv"
    echo   ✓ Removed backend\venv
) else (
    echo   ℹ backend\venv not found
)

echo.
echo [3/4] Removing unnecessary test/utility scripts from backend...
del /F /Q "backend\check_dependencies.py" 2>nul
del /F /Q "backend\diagnose_bot.py" 2>nul
del /F /Q "backend\install_deps.py" 2>nul
del /F /Q "backend\quick_test.py" 2>nul
del /F /Q "backend\test_all.py" 2>nul
del /F /Q "backend\test_dataset_accuracy.py" 2>nul
del /F /Q "backend\test_multi_search.py" 2>nul
del /F /Q "backend\test_suggestions.py" 2>nul
del /F /Q "backend\verify_env.py" 2>nul
del /F /Q "backend\verify_setup.py" 2>nul
del /F /Q "backend\run_app.py" 2>nul
del /F /Q "backend\simple_app.py" 2>nul
del /F /Q "backend\setup.py" 2>nul
echo   ✓ Removed development utility scripts

echo.
echo [4/5] Removing old cleanup scripts...
del /F /Q "cleanup_docs.bat" 2>nul
del /F /Q "fix_and_start.bat" 2>nul
del /F /Q "fix_and_start.ps1" 2>nul
echo   ✓ Removed old cleanup/fix scripts

echo.
echo [5/5] Removing __pycache__ directories...
if exist "backend\__pycache__" (
    rmdir /S /Q "backend\__pycache__"
    echo   ✓ Removed backend\__pycache__
)
echo   ✓ Cache cleanup complete

echo.
echo ========================================
echo Cleanup completed successfully!
echo ========================================
echo.
echo Summary:
echo   - Removed 20 redundant .md files
echo   - Removed duplicate backend\venv
echo   - Removed 13 development utility scripts
echo   - Removed 3 old cleanup/fix scripts
echo   - Removed cache directories
echo.
echo Questionable folders:
echo   - "login nyayshield\" folder contains PHP files
echo     (If this is not part of your project, delete it manually)
echo.
echo Your project is now clean and organized!
echo Main documentation: docs\README.md
echo.
pause
