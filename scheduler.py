"""
AI 뉴스 스케줄러 — 매일 오전 9시 KST 자동 발송
nohup python scheduler.py &
"""

import time
import io
import sys
from datetime import datetime, timezone, timedelta

# UTF-8 출력
if sys.stdout.encoding != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
if sys.stderr.encoding != "utf-8":
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

KST = timezone(timedelta(hours=9))
TARGET_HOUR = 9   # 오전 9시 KST


def seconds_until_next_run() -> float:
    """다음 오전 9시 KST까지 남은 초"""
    now = datetime.now(KST)
    next_run = now.replace(hour=TARGET_HOUR, minute=0, second=0, microsecond=0)
    if now >= next_run:
        # 이미 9시 지났으면 내일 9시
        next_run += timedelta(days=1)
    delta = (next_run - now).total_seconds()
    return delta


def main():
    print(f"[Scheduler] 시작 — 매일 오전 {TARGET_HOUR}시 KST에 뉴스를 발송합니다.")
    print(f"[Scheduler] 현재 시각: {datetime.now(KST).strftime('%Y-%m-%d %H:%M:%S KST')}")

    while True:
        wait_sec = seconds_until_next_run()
        next_time = datetime.now(KST) + timedelta(seconds=wait_sec)
        print(f"[Scheduler] 다음 발송: {next_time.strftime('%Y-%m-%d %H:%M KST')} ({wait_sec/3600:.1f}시간 후)")
        sys.stdout.flush()

        time.sleep(wait_sec)

        # 발송 실행
        print(f"\n[Scheduler] ⏰ 오전 9시 도달 — 뉴스 브리핑 시작")
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
