# Nyaya-Shield Auto Fix and Start Script
# PowerShell version for better error handling

Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host "NYAYA-SHIELD AUTO FIX AND START" -ForegroundColor Cyan
Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host ""

# Navigate to backend directory
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location "$scriptPath\backend"

Write-Host "Step 1: Retraining all models (this may take 2-5 minutes)..." -ForegroundColor Yellow
Write-Host "================================================================================" -ForegroundColor Gray
try {
    python -m bot.train_enhanced_models
    if ($LASTEXITCODE -eq 0) {
        Write-Host ""
        Write-Host "✓ Models retrained successfully!" -ForegroundColor Green
        Write-Host ""
    } else {
        throw "Model training failed with exit code $LASTEXITCODE"
    }
} catch {
    Write-Host "ERROR: Model training failed!" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host "Step 2: Verifying models work correctly..." -ForegroundColor Yellow
Write-Host "================================================================================" -ForegroundColor Gray
try {
    python -m bot.verify_dataset_response
    Write-Host ""
    Write-Host "✓ Verification complete!" -ForegroundColor Green
    Write-Host ""
} catch {
    Write-Host "WARNING: Verification had issues, but continuing..." -ForegroundColor Yellow
}

Write-Host "Step 3: Starting server..." -ForegroundColor Yellow
Write-Host "================================================================================" -ForegroundColor Gray
Write-Host "Server will start now. Press Ctrl+C to stop when needed." -ForegroundColor White
Write-Host ""
Write-Host "IMPORTANT: Use domain-specific pages for best results:" -ForegroundColor Cyan
Write-Host "  - CrPC (arrest, FIR, bail): " -NoNewline -ForegroundColor White
Write-Host "http://localhost:5000/services/crpc_chat" -ForegroundColor Green
Write-Host "  - IPC (sections, crimes): " -NoNewline -ForegroundColor White
Write-Host "http://localhost:5000/services/ipc_chat" -ForegroundColor Green
Write-Host "  - Consumer: " -NoNewline -ForegroundColor White
Write-Host "http://localhost:5000/services/consumer_chat" -ForegroundColor Green
Write-Host "  - Family: " -NoNewline -ForegroundColor White
Write-Host "http://localhost:5000/services/family_chat" -ForegroundColor Green
Write-Host "  - Property: " -NoNewline -ForegroundColor White
Write-Host "http://localhost:5000/services/property_chat" -ForegroundColor Green
Write-Host "  - Cyber: " -NoNewline -ForegroundColor White
Write-Host "http://localhost:5000/services/cyber_chat" -ForegroundColor Green
Write-Host ""
Write-Host "================================================================================" -ForegroundColor Gray
Write-Host ""

# Start the server
python app.py
