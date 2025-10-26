@echo off
echo ================================================================================
echo CLEANING UP UNNECESSARY DOCUMENTATION FILES
echo ================================================================================
echo.

cd /d "%~dp0"

echo Deleting duplicate/unnecessary MD files...
echo.

REM Delete duplicate fix guides (keeping only AUTO_FIX_README.md)
if exist "CRITICAL_FIX_NEEDED.md" del "CRITICAL_FIX_NEEDED.md" && echo Deleted: CRITICAL_FIX_NEEDED.md
if exist "FIX_NOW.md" del "FIX_NOW.md" && echo Deleted: FIX_NOW.md
if exist "FIX_GUIDE.md" del "FIX_GUIDE.md" && echo Deleted: FIX_GUIDE.md
if exist "FIXES_APPLIED.md" del "FIXES_APPLIED.md" && echo Deleted: FIXES_APPLIED.md
if exist "FINAL_FIX_APPLIED.md" del "FINAL_FIX_APPLIED.md" && echo Deleted: FINAL_FIX_APPLIED.md

REM Delete duplicate training guides (keeping only ENHANCED_TRAINING_GUIDE.md)
if exist "READY_TO_TRAIN.md" del "READY_TO_TRAIN.md" && echo Deleted: READY_TO_TRAIN.md

REM Delete duplicate response guides (keeping only USER_FRIENDLY_RESPONSES.md)
if exist "ENSURE_SPECIFIC_REPLIES.md" del "ENSURE_SPECIFIC_REPLIES.md" && echo Deleted: ENSURE_SPECIFIC_REPLIES.md
if exist "ENHANCED_RESPONSES_ALL_DOMAINS.md" del "ENHANCED_RESPONSES_ALL_DOMAINS.md" && echo Deleted: ENHANCED_RESPONSES_ALL_DOMAINS.md

REM Delete duplicate verification guides (keeping only ENSURE_DATASET_ANSWERS.md)
if exist "YOUR_BOT_IS_READY.md" del "YOUR_BOT_IS_READY.md" && echo Deleted: YOUR_BOT_IS_READY.md

REM Delete old implementation docs (keeping only FEATURE_COMPLETE.md)
if exist "IMPLEMENTATION_SUMMARY.md" del "IMPLEMENTATION_SUMMARY.md" && echo Deleted: IMPLEMENTATION_SUMMARY.md
if exist "VERIFICATION_REPORT.md" del "VERIFICATION_REPORT.md" && echo Deleted: VERIFICATION_REPORT.md

echo.
echo ================================================================================
echo CLEANUP COMPLETE
echo ================================================================================
echo.
echo Kept essential files:
echo   - AUTO_FIX_README.md (How to run the bot)
echo   - ENHANCED_TRAINING_GUIDE.md (Training guide)
echo   - USER_FRIENDLY_RESPONSES.md (Response examples)
echo   - ENSURE_DATASET_ANSWERS.md (Verification guide)
echo   - FEATURE_COMPLETE.md (Features documentation)
echo   - QUICK_START.md (Quick start guide)
echo   - QUICK_TEST_GUIDE.md (Test questions)
echo   - TEST_QUESTIONS.md (Test questions)
echo   - MULTI_DATASET_SEARCH.md (Search documentation)
echo.
pause
