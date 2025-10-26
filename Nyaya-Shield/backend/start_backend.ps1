param(
  [int]$Port = 5000,
  [string]$DatasetThreshold = "0.25",
  [ValidateSet("true","false")][string]$EnableLLM = "false",
  [ValidateSet("true","false")][string]$AutoTrain = "false",
  [ValidateSet("true","false")][string]$PipelineTrace = "true"
)

$ErrorActionPreference = 'Stop'

function Write-Info($msg) { Write-Host "[INFO ] $msg" -ForegroundColor Cyan }
function Write-OK($msg)   { Write-Host "[ OK  ] $msg" -ForegroundColor Green }
function Write-Warn($msg) { Write-Host "[WARN ] $msg" -ForegroundColor Yellow }
function Write-Err($msg)  { Write-Host "[ERR  ] $msg" -ForegroundColor Red }

# Resolve paths
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoRoot  = Split-Path -Parent $ScriptDir
$VenvDir   = Join-Path $RepoRoot 'venv'
$PyExe     = Join-Path $VenvDir 'Scripts\python.exe'
$Activate  = Join-Path $VenvDir 'Scripts\Activate.ps1'
$AppFile   = Join-Path $ScriptDir 'run_app.py'
$HealthUrl = "http://127.0.0.1:$Port/health"

Write-Info "Backend dir: $ScriptDir"
Write-Info "Repo root  : $RepoRoot"

if (!(Test-Path $PyExe)) { Write-Err "Python venv not found at $PyExe"; exit 1 }
if (!(Test-Path $AppFile)) { Write-Err "run_app.py not found at $AppFile"; exit 1 }

# Activate venv
Write-Info "Activating venv..."
. $Activate

# Env vars
$env:AUTO_TRAIN       = $AutoTrain
$env:ENABLE_LLM       = $EnableLLM
$env:PORT             = "$Port"
$env:DATASET_THRESHOLD= $DatasetThreshold
$env:PIPELINE_TRACE   = $PipelineTrace
Write-Info "ENV: AUTO_TRAIN=$($env:AUTO_TRAIN) ENABLE_LLM=$($env:ENABLE_LLM) PORT=$($env:PORT) DATASET_THRESHOLD=$($env:DATASET_THRESHOLD) PIPELINE_TRACE=$($env:PIPELINE_TRACE)"

# Kill old process on port if exists
Write-Info "Checking port $Port..."
$pidLine = netstat -ano | Select-String ":$Port" | Select-Object -First 1
if ($pidLine) {
  $parts = ($pidLine -split "\s+") | Where-Object { $_ -ne '' }
  $processId = $parts[-1]
  if ($processId -match '^[0-9]+$') {
    Write-Warn "Killing existing process PID=$processId on port $Port"
    try { taskkill /PID $processId /F | Out-Null } catch { Write-Warn "taskkill failed or process already ended" }
  }
}

# Start server
Write-Info "Starting server..."
$startInfo = New-Object System.Diagnostics.ProcessStartInfo
$startInfo.FileName = $PyExe
$startInfo.Arguments = "`"$AppFile`""
$startInfo.WorkingDirectory = $ScriptDir
$startInfo.UseShellExecute = $false
$startInfo.RedirectStandardOutput = $true
$startInfo.RedirectStandardError  = $true
$proc = New-Object System.Diagnostics.Process
$proc.StartInfo = $startInfo
$null = $proc.Start()

# Tail a little output asynchronously
Start-Job -ScriptBlock {
  param($p)
  try { while(-not $p.HasExited){ if(!$p.StandardOutput.EndOfStream){ $line=$p.StandardOutput.ReadLine(); if($line){ Write-Host "[SRV ] $line" } } Start-Sleep -Milliseconds 100 } } catch {}
} -ArgumentList $proc | Out-Null

# Wait for health
Write-Info "Polling health: $HealthUrl"
$deadline = (Get-Date).AddSeconds(30)
$healthy = $false
while((Get-Date) -lt $deadline) {
  try {
    $resp = Invoke-RestMethod -Uri $HealthUrl -TimeoutSec 2
    if ($resp -and $resp.services -and $resp.services.bot_controller -and $resp.services.nlp_service) {
      Write-OK "Health OK. Model loaded: $($resp.services.model_loaded) QA: $($resp.model_info.qa_pairs_count)"
      $healthy = $true
      break
    }
  } catch { Start-Sleep -Milliseconds 500 }
}

if (-not $healthy) { Write-Warn "Server not healthy yet. Check logs above." }
else { Write-OK "Backend ready at http://127.0.0.1:$Port" }

Write-Info "Press Ctrl+C in this window to stop the server."
