"""
AI 뉴스 스케줄러 — 매일 지정한 KST 시각 자동 발송
nohup python scheduler.py &
"""

import atexit
import fcntl
import io
import os
import sys
import time
from datetime import datetime, timezone, timedelta

# UTF-8 출력
if sys.stdout.encoding != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
if sys.stderr.encoding != "utf-8":
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

from dotenv import load_dotenv
load_dotenv()

KST = timezone(timedelta(hours=9))
APP_DIR = os.path.dirname(os.path.abspath(__file__))
LOCK_PATH = os.path.join(APP_DIR, "scheduler.lock")

# SEND_TIME=HH:MM 형식 (기본값 11:00 KST)
_send_time = os.environ.get("SEND_TIME", "11:00")
try:
    _h, _m = _send_time.strip().split(":")
    TARGET_HOUR = int(_h)
    TARGET_MINUTE = int(_m)
    if not (0 <= TARGET_HOUR <= 23 and 0 <= TARGET_MINUTE <= 59):
        raise ValueError
except ValueError:
    print(f"[Scheduler] ❌ SEND_TIME 형식 오류: {_send_time!r}. 예: SEND_TIME=11:00")
    sys.exit(1)


_lock_file = None


def acquire_single_instance_lock() -> None:
    """스케줄러 중복 실행 방지. 이미 실행 중이면 즉시 종료."""
    global _lock_file
    _lock_file = open(LOCK_PATH, "w", encoding="utf-8")
    try:
        fcntl.flock(_lock_file, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        print("[Scheduler] ⚠️ 이미 실행 중인 scheduler.py가 있습니다. 중복 실행을 막고 종료합니다.")
        print("             기존 프로세스를 끄려면: bash run.sh stop 또는 pkill -f scheduler.py")
        sys.exit(0)

    _lock_file.write(str(os.getpid()))
    _lock_file.flush()
    atexit.register(release_single_instance_lock)


def release_single_instance_lock() -> None:
    global _lock_file
    if _lock_file:
        try:
            fcntl.flock(_lock_file, fcntl.LOCK_UN)
            _lock_file.close()
        except Exception:
            pass


def seconds_until_next_run() -> float:
    """다음 발송 시각까지 남은 초"""
    now = datetime.now(KST)
    next_run = now.replace(hour=TARGET_HOUR, minute=TARGET_MINUTE, second=0, microsecond=0)
    if now >= next_run:
        next_run += timedelta(days=1)
    delta = (next_run - now).total_seconds()
    return max(delta, 0)


def main():
    acquire_single_instance_lock()

    print(f"[Scheduler] 시작 — 매일 {TARGET_HOUR:02d}:{TARGET_MINUTE:02d} KST에 뉴스를 발송합니다. (.env SEND_TIME={_send_time})")
    print(f"[Scheduler] 현재 시각: {datetime.now(KST).strftime('%Y-%m-%d %H:%M:%S KST')}")
    print(f"[Scheduler] PID: {os.getpid()} / lock: {LOCK_PATH}")

    while True:
        wait_sec = seconds_until_next_run()
        next_time = datetime.now(KST) + timedelta(seconds=wait_sec)
        print(f"[Scheduler] 다음 발송: {next_time.strftime('%Y-%m-%d %H:%M KST')} ({wait_sec/3600:.1f}시간 후)")
        sys.stdout.flush()

        time.sleep(wait_sec)

        # ── sleep 조기 종료 방지: 실제 목표 시각에 도달했는지 확인 ──
        _now = datetime.now(KST)
        _target_today = _now.replace(hour=TARGET_HOUR, minute=TARGET_MINUTE, second=0, microsecond=0)
        _elapsed = (_now - _target_today).total_seconds()
        if _elapsed < -30:  # 목표 시각까지 30초 이상 남았으면 조기 종료된 sleep
            print(f"[Scheduler] ⚠️  sleep 조기 종료 감지 (현재: {_now.strftime('%H:%M')}, 목표: {TARGET_HOUR:02d}:{TARGET_MINUTE:02d}, {-_elapsed/60:.1f}분 남음). 계속 대기...")
            continue

        # 발송 실행
        print(f"\n[Scheduler] ⏰ {TARGET_HOUR:02d}:{TARGET_MINUTE:02d} 도달 — 뉴스 브리핑 시작")
        sys.stdout.flush()
        try:
            from main import run_daily_briefing
            run_daily_briefing()
        except Exception as e:
            print(f"[Scheduler] ❌ 오류 발생: {e}")
            import traceback
            traceback.print_exc()
        finally:
            sys.stdout.flush()

        # 같은 분에 반복 발송되는 것을 방지
        time.sleep(60)


if __name__ == "__main__":
    main()
