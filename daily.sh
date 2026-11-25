#!/bin/bash
# Daily watchlist job (macOS port of daily.ps1). Scheduled at 12:00 by launchd via schedule.sh.
# Run by hand: ./daily.sh
cd "$(dirname "$0")" || exit 1
root="$PWD"
export PATH="/opt/local/bin:$HOME/.local/bin:/usr/bin:/bin:$PATH"  # launchd starts with a bare PATH
mkdir -p logs
log="$root/logs/daily.log"  # absolute: the claude step runs from a scratch folder
say() { echo "$(date +%Y-%m-%dT%H:%M:%S) $*" | tee -a "$log"; }
step() { "$@" >>"$log" 2>&1 || fail "$1 failed (exit $?)"; }
fail() {
  git checkout -- today.json index.html >/dev/null 2>&1  # keep yesterday's issue as the base for tomorrow
  say "FAIL $*"
  exit 1
}

say "start"
step git pull --ff-only
step python3 build.py

# Claude curates in a scratch folder holding only its inputs, so text from the
# feeds cannot steer it into editing the repo's code or reading other files.
work="${TMPDIR:-/tmp}/intellia-watchlist-curate"
rm -rf "$work" && mkdir -p "$work"
cp editorial.md pool.json "$work/"
[ -f today.json ] && cp today.json "$work/"
(cd "$work" && claude -p --allowedTools "Read,Write" --permission-mode acceptEdits <"$root/prompt.md") >>"$log" 2>&1 \
  || fail "claude failed (exit $?)"
cmp -s "$work/today.json" today.json && fail "today.json unchanged"
cp "$work/today.json" today.json

step python3 render.py
step git add today.json index.html
step git commit -m "daily: $(date +%Y-%m-%d)"
step git push
say "ok"

if [ -f slack-webhook.txt ]; then
  # Post at 12:15, or 90 seconds after the push if the run started late,
  # so GitHub Pages has published before people click the link.
  wait=$(( $(date -j -f %H:%M 12:15 +%s) - $(date +%s) ))
  [ "$wait" -lt 90 ] && wait=90
  say "slack posts in ${wait}s"
  sleep "$wait"
  if python3 notify.py >>"$log" 2>&1; then say "slack ok"; else say "slack FAIL"; fi  # the page is live either way
fi
