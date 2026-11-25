#!/bin/bash
# Registers the daily noon job with launchd (macOS port of schedule.ps1). Run once: ./schedule.sh
# Runs only while you are logged in (it needs your Claude Code login).
# If the Mac is asleep at noon, it runs when it wakes; if it is shut down, that day is skipped.
here="$(cd "$(dirname "$0")" && pwd)"
plist="$HOME/Library/LaunchAgents/com.intellia.watchlist.plist"
cat >"$plist" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key><string>com.intellia.watchlist</string>
  <key>ProgramArguments</key><array><string>/bin/bash</string><string>$here/daily.sh</string></array>
  <key>StartCalendarInterval</key><dict><key>Hour</key><integer>12</integer><key>Minute</key><integer>0</integer></dict>
  <key>StandardOutPath</key><string>$here/logs/launchd.log</string>
  <key>StandardErrorPath</key><string>$here/logs/launchd.log</string>
</dict>
</plist>
EOF
launchctl bootout "gui/$(id -u)/com.intellia.watchlist" 2>/dev/null
launchctl bootstrap "gui/$(id -u)" "$plist" && echo "scheduled: $plist"
