"""
AI 뉴스 스케줄러 — 매일 오전 9시 KST 자동 발송
nohup python scheduler.py &
"""

import time
import io
import sys
import os
from datetime import datetime, timezone, timedelta

# UTF-8 출력
if sys.stdout.encoding != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
if sys.stderr.encoding != "utf-8":
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

from dotenv import load_dotenv
load_dotenv()

KST = timezone(timedelta(hours=9))

# SEND_TIME=HH:MM 형식 (기본값 09:00 KST)
_send_time = os.environ.get("SEND_TIME", "09:00")
_h, _m = _send_time.strip().split(":")
TARGET_HOUR = int(_h)
TARGET_MINUTE = int(_m)


def seconds_until_next_run() -> float:
    """다음 발송 시각까지 남은 초"""
    now = datetime.now(KST)
    next_run = now.replace(hour=TARGET_HOUR, minute=TARGET_MINUTE, second=0, microsecond=0)
    if now >= next_run:
        next_run += timedelta(days=1)
    delta = (next_run - now).total_seconds()
    return delta


def main():
    print(f"[Scheduler] 시작 — 매일 {TARGET_HOUR:02d}:{TARGET_MINUTE:02d} KST에 뉴스를 발송합니다. (.env SEND_TIME={_send_time})")
    print(f"[Scheduler] 현재 시각: {datetime.now(KST).strftime('%Y-%m-%d %H:%M:%S KST')}")

    while True:
        wait_sec = seconds_until_next_run()
        next_time = datetime.now(KST) + timedelta(seconds=wait_sec)
        print(f"[Scheduler] 다음 발송: {next_time.strftime('%Y-%m-%d %H:%M KST')} ({wait_sec/3600:.1f}시간 후)")
        sys.stdout.flush()

        time.sleep(wait_sec)

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

        # 중복 실행 방지: 1분 대기 후 다음 루프
        time.sleep(60)


if __name__ == "__main__":
    main()
