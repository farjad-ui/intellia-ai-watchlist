# Registers the daily noon job in Windows Task Scheduler. Run once:
#   powershell -ExecutionPolicy Bypass -File schedule.ps1
# Runs only while you are logged in (it needs your Claude Code login).
# If the laptop is off at noon, it runs as soon as you next log in.
$action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument "-NoProfile -ExecutionPolicy Bypass -File `"$PSScriptRoot\daily.ps1`"" -WorkingDirectory $PSScriptRoot
$trigger = New-ScheduledTaskTrigger -Daily -At 12:00
$settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -ExecutionTimeLimit (New-TimeSpan -Minutes 30)
Register-ScheduledTask -TaskName "Intellia AI Watchlist" -Action $action -Trigger $trigger -Settings $settings -Force | Out-Null
Get-ScheduledTask -TaskName "Intellia AI Watchlist" | Get-ScheduledTaskInfo | Select-Object TaskName, NextRunTime
