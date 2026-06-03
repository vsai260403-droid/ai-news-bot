#!/usr/bin/env bash
set -u

APP_DIR="/home/pi/dis_server/ai-news-bot"
LOG_DIR="$APP_DIR/logs"
NAME="$1"
SCRIPT="$2"
CRASH_LOG="$LOG_DIR/systemd-crash.log"

cd "$APP_DIR"
mkdir -p "$LOG_DIR"

export PYTHONUNBUFFERED=1
export PYTHONFAULTHANDLER=1

START_TS="$(date '+%Y-%m-%d %H:%M:%S %Z')"
START_EPOCH="$(date +%s)"

echo "============================================================" >> "$CRASH_LOG"
echo "[$START_TS] START name=$NAME script=$SCRIPT pid=$$" >> "$CRASH_LOG"
echo "cwd=$(pwd)" >> "$CRASH_LOG"
echo "python=$(command -v python3)" >> "$CRASH_LOG"
python3 --version >> "$CRASH_LOG" 2>&1

python3 -u "$SCRIPT"
STATUS=$?

END_TS="$(date '+%Y-%m-%d %H:%M:%S %Z')"
END_EPOCH="$(date +%s)"
UPTIME=$((END_EPOCH - START_EPOCH))

{
  echo "[$END_TS] EXIT name=$NAME script=$SCRIPT status=$STATUS uptime=${UPTIME}s"
  echo "--- memory ---"
  free -h || true
  echo "--- disk ---"
  df -h "$APP_DIR" || true
  echo "--- last bot.log ---"
  tail -n 80 "$LOG_DIR/bot.log" 2>/dev/null || true
  echo "--- last scheduler.log ---"
  tail -n 80 "$LOG_DIR/scheduler.log" 2>/dev/null || true
  echo "============================================================"
} >> "$CRASH_LOG" 2>&1

exit "$STATUS"
