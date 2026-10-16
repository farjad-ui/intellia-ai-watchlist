# Daily watchlist job. Scheduled at 12:00 by Task Scheduler as "Intellia AI Watchlist".
# Run by hand: powershell -ExecutionPolicy Bypass -File daily.ps1
$ErrorActionPreference = "Continue"  # native tools write progress to stderr; exit codes decide failure
$OutputEncoding = [Text.UTF8Encoding]::new($false)  # PowerShell 5.1 pipes ASCII to native programs by default
Set-Location $PSScriptRoot
New-Item -ItemType Directory -Force logs | Out-Null
$log = Join-Path $PSScriptRoot "logs\daily.log"  # absolute: the claude step runs from a scratch folder
function Log($m) { Add-Content $log "$(Get-Date -Format s) $m" -Encoding utf8; Write-Host $m }
function Step($name, [scriptblock]$cmd) {
  & $cmd 2>&1 | ForEach-Object { "$_" } | Add-Content $log -Encoding utf8
  if ($LASTEXITCODE) { throw "$name failed (exit $LASTEXITCODE)" }
}

try {
  Log "start"
  Step "git pull" { git pull --ff-only }
  Step "build" { python build.py }

  # Claude curates in a scratch folder holding only its inputs, so text from the
  # feeds cannot steer it into editing the repo's code or reading other files.
  $work = Join-Path $env:TEMP "intellia-watchlist-curate"
  Remove-Item $work -Recurse -Force -ErrorAction SilentlyContinue
  New-Item -ItemType Directory $work | Out-Null
  Copy-Item editorial.md, pool.json $work
  if (Test-Path today.json) { Copy-Item today.json $work }
  $before = if (Test-Path today.json) { (Get-FileHash today.json).Hash } else { "" }
  Push-Location $work
  try {
    # The prompt goes in on stdin: PowerShell 5.1 cuts native arguments at the first double quote.
    Step "claude" { Get-Content "$PSScriptRoot\prompt.md" -Raw | claude -p --allowedTools "Read,Write" --permission-mode acceptEdits }
  } finally { Pop-Location }
  Copy-Item (Join-Path $work today.json) today.json -Force
  if ((Get-FileHash today.json).Hash -eq $before) { throw "today.json unchanged" }

  Step "render" { python render.py }
  Step "git add" { git add today.json index.html }
  Step "git commit" { git commit -m "daily: $(Get-Date -Format yyyy-MM-dd)" }
  Step "git push" { git push }
  Log "ok"
  if (Test-Path slack-webhook.txt) {
    # Post at 12:15, or 90 seconds after the push if the run started late,
    # so GitHub Pages has published before people click the link.
    $postAt = (Get-Date).Date.AddHours(12).AddMinutes(15)
    $wait = [Math]::Max(90, ($postAt - (Get-Date)).TotalSeconds)
    Log "slack posts at $((Get-Date).AddSeconds($wait).ToString('HH:mm'))"
    Start-Sleep -Seconds $wait
    try { Step "slack" { python notify.py }; Log "slack ok" } catch { Log "slack FAIL $_" }  # the page is live either way
  }
} catch {
  git checkout -- today.json index.html 2>&1 | Out-Null  # keep yesterday's issue as the base for tomorrow
  Log "FAIL $_"
  exit 1
}
