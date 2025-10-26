# Nyaya-Shield Cleanup Script
Write-Host ""
Write-Host "========================================"  -ForegroundColor Cyan
Write-Host "Nyaya-Shield Project Cleanup"  -ForegroundColor Cyan
Write-Host "========================================"  -ForegroundColor Cyan
Write-Host ""

$removedCount = 0

# 1. Remove redundant .md files
Write-Host "[1/5] Removing redundant .md documentation files..." -ForegroundColor Yellow
$mdFiles = @(
    "AUTO_FIX_README.md",
    "CRITICAL_FIX_NEEDED.md",
    "ENHANCED_RESPONSES_ALL_DOMAINS.md",
    "ENHANCED_TRAINING_GUIDE.md",
    "ENSURE_DATASET_ANSWERS.md",
    "ENSURE_SPECIFIC_REPLIES.md",
    "FEATURE_COMPLETE.md",
    "FINAL_FIX_APPLIED.md",
    "FIXES_APPLIED.md",
    "FIX_GUIDE.md",
    "FIX_NOW.md",
    "IMPLEMENTATION_SUMMARY.md",
    "MULTI_DATASET_SEARCH.md",
    "QUICK_START.md",
    "QUICK_TEST_GUIDE.md",
    "READY_TO_TRAIN.md",
    "TEST_QUESTIONS.md",
    "USER_FRIENDLY_RESPONSES.md",
    "VERIFICATION_REPORT.md",
    "YOUR_BOT_IS_READY.md"
)

foreach ($file in $mdFiles) {
    if (Test-Path $file) {
        Remove-Item $file -Force
        $removedCount++
    }
}
Write-Host "  ✓ Removed $removedCount redundant .md files" -ForegroundColor Green
Write-Host ""

# 2. Remove duplicate backend\venv
Write-Host "[2/5] Checking for duplicate backend\venv directory..." -ForegroundColor Yellow
if (Test-Path "backend\venv") {
    Write-Host "  Found backend\venv (approx 1-2GB)" -ForegroundColor Yellow
    Write-Host "  Removing... this may take a minute..." -ForegroundColor Yellow
    Remove-Item "backend\venv" -Recurse -Force
    Write-Host "  ✓ Removed backend\venv" -ForegroundColor Green
} else {
    Write-Host "  ℹ backend\venv not found (already clean)" -ForegroundColor Gray
}
Write-Host ""

# 3. Remove unnecessary test scripts
Write-Host "[3/5] Removing unnecessary test/utility scripts..." -ForegroundColor Yellow
$testScripts = @(
    "backend\check_dependencies.py",
    "backend\diagnose_bot.py",
    "backend\install_deps.py",
    "backend\quick_test.py",
    "backend\test_all.py",
    "backend\test_dataset_accuracy.py",
    "backend\test_multi_search.py",
    "backend\test_suggestions.py",
    "backend\verify_env.py",
    "backend\verify_setup.py",
    "backend\run_app.py",
    "backend\simple_app.py",
    "backend\setup.py"
)

$testRemoved = 0
foreach ($file in $testScripts) {
    if (Test-Path $file) {
        Remove-Item $file -Force
        $testRemoved++
    }
}
Write-Host "  ✓ Removed $testRemoved development utility scripts" -ForegroundColor Green
Write-Host ""

# 4. Remove old cleanup scripts
Write-Host "[4/5] Removing old cleanup scripts..." -ForegroundColor Yellow
$oldScripts = @(
    "cleanup_docs.bat",
    "fix_and_start.bat",
    "fix_and_start.ps1",
    "cleanup_redundant_files.bat"
)

$oldRemoved = 0
foreach ($file in $oldScripts) {
    if (Test-Path $file) {
        Remove-Item $file -Force
        $oldRemoved++
    }
}
Write-Host "  ✓ Removed $oldRemoved old cleanup/fix scripts" -ForegroundColor Green
Write-Host ""

# 5. Remove cache directories
Write-Host "[5/5] Removing __pycache__ directories..." -ForegroundColor Yellow
if (Test-Path "backend\__pycache__") {
    Remove-Item "backend\__pycache__" -Recurse -Force
    Write-Host "  ✓ Removed backend\__pycache__" -ForegroundColor Green
}
Write-Host "  ✓ Cache cleanup complete" -ForegroundColor Green
Write-Host ""

# Summary
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Cleanup completed successfully!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Summary:" -ForegroundColor White
Write-Host "  - Removed $removedCount redundant .md files" -ForegroundColor White
Write-Host "  - Checked/removed duplicate backend\venv" -ForegroundColor White
Write-Host "  - Removed $testRemoved development utility scripts" -ForegroundColor White
Write-Host "  - Removed $oldRemoved old cleanup/fix scripts" -ForegroundColor White
Write-Host "  - Removed cache directories" -ForegroundColor White
Write-Host ""
Write-Host "Questionable folders:" -ForegroundColor Yellow
Write-Host "  - 'login nyayshield\' folder contains PHP files" -ForegroundColor Yellow
Write-Host "    (If this is not part of your project, delete it manually)" -ForegroundColor Yellow
Write-Host ""
Write-Host "Your project is now clean and organized!" -ForegroundColor Green
Write-Host "Main documentation: docs\README.md" -ForegroundColor Cyan
Write-Host ""
