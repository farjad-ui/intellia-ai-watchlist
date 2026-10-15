# Daily watchlist job. Scheduled at 12:00 by Task Scheduler as "Intellia AI Watchlist".
# Run by hand: powershell -ExecutionPolicy Bypass -File daily.ps1
$ErrorActionPreference = "Stop"
$OutputEncoding = [Text.UTF8Encoding]::new($false)  # PowerShell 5.1 pipes ASCII to native programs by default
Set-Location $PSScriptRoot
New-Item -ItemType Directory -Force logs | Out-Null
function Log($m) { Add-Content logs\daily.log "$(Get-Date -Format s) $m"; Write-Host $m }

try {
  git pull --ff-only
  if ($LASTEXITCODE) { throw "git pull failed" }
  python build.py
  if ($LASTEXITCODE) { throw "build.py failed" }

  $before = if (Test-Path today.json) { (Get-FileHash today.json).Hash } else { "" }
  # The prompt goes in on stdin: PowerShell 5.1 cuts native arguments at the first double quote.
  Get-Content prompt.md -Raw | claude -p --allowedTools "Read,Write" --permission-mode acceptEdits
  if ($LASTEXITCODE) { throw "claude failed" }
  if ((Get-FileHash today.json).Hash -eq $before) { throw "today.json unchanged" }

  python render.py
  if ($LASTEXITCODE) { throw "render.py failed" }
  git add today.json index.html
  git commit -m "daily: $(Get-Date -Format yyyy-MM-dd)"
  git push
  if ($LASTEXITCODE) { throw "git push failed" }
  Log "ok"
} catch {
  Log "FAIL $_"
  exit 1
}
