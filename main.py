"""
AI 뉴스 데일리 디스코드 봇 — 메인 실행 & 스케줄러

사용법:
    python main.py           # 스케줄러 모드 (매일 자동 실행)
    python main.py --now     # 즉시 실행
    python main.py --dry-run # 수집 & 요약만 (전송하지 않음)
    python main.py --test    # 디스코드 테스트 메시지 전송
"""

import argparse
import io
import sys
import time
from datetime import datetime, timezone, timedelta

# Windows 콘솔 UTF-8 출력 설정 (이모지/한글 깨짐 방지)
if sys.stdout.encoding != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
if sys.stderr.encoding != "utf-8":
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

import schedule

from config import DISCORD_WEBHOOK_URL, GEMINI_API_KEY, MAX_ARTICLES, SEND_TIME
from collector import fetch_articles, save_sent_articles, _load_sent_articles
from summarizer import summarize_articles
from discord_sender import send_to_discord, send_test_message


KST = timezone(timedelta(hours=9))


def run_daily_briefing(dry_run: bool = False):
    """메인 실행: 수집 → 요약 → 전송"""
    now = datetime.now(KST).strftime("%Y-%m-%d %H:%M KST")
    print(f"\n{'='*50}")
    print(f"🚀 AI 뉴스 데일리 브리핑 시작 — {now}")
    print(f"{'='*50}")

    # 1. 뉴스 수집
    print("\n📡 Step 1: RSS 피드에서 뉴스 수집")
    articles = fetch_articles(hours=24)

    if not articles:
        print("\n😴 새로운 AI 뉴스가 없습니다.")
        return

    # 2. LLM 분류 후 충분한 후보 확보 (MAX_ARTICLES * 3)
    candidate_count = MAX_ARTICLES * 3
    articles = articles[:candidate_count]
    print(f"\n📋 Step 2: LLM 분류 후보 {len(articles)}개 선정 (목표: {MAX_ARTICLES}개)")

    for i, art in enumerate(articles, 1):
        print(f"  {i}. [{art['source_name']}] {art['title'][:60]}...")

    # 3. AI 분류 + 요약 (비즈니스 뉴스 자동 제외)
    print("\n🤖 Step 3: Gemini API로 기사 분류 및 한국어 요약 생성")
    articles = summarize_articles(articles)

    # 최종 상위 N개 제한
    articles = articles[:MAX_ARTICLES]

    # 4. 디스코드 전송
    if dry_run:
        print("\n🔍 [DRY RUN] 디스코드 전송을 건너뜁니다.")
        print("\n── 수집된 기사 미리보기 ──")
        for i, art in enumerate(articles, 1):
            print(f"\n{'─'*40}")
            print(f"{i}. {art['source_emoji']} [{art['source_name']}]")
            print(f"   📰 {art['title']}")
            print(f"   🔗 {art['url']}")
            if art.get("ai_summary"):
                print(f"   📝 {art['ai_summary']}")
    else:
        print("\n📨 Step 4: 디스코드로 전송")
        success = send_to_discord(articles)
        if success:
            # 전송 성공 시 이력 저장
            sent = _load_sent_articles()
            now_iso = datetime.now(timezone.utc).isoformat()
            for art in articles:
                sent[art["url"]] = now_iso
            save_sent_articles(sent)
            print("\n💾 전송 이력 저장 완료")

    print(f"\n{'='*50}")
    print(f"✅ 브리핑 완료!")
    print(f"{'='*50}\n")


def run_scheduler():
    """매일 지정 시간에 자동 실행"""
    print(f"⏰ 스케줄러 시작 — 매일 {SEND_TIME} (KST)에 실행됩니다.")
    print(f"   Ctrl+C 로 종료\n")

    # 설정 확인
    if not DISCORD_WEBHOOK_URL:
        print("❌ 오류: .env 파일에 DISCORD_WEBHOOK_URL을 설정해주세요.")
        sys.exit(1)

    # SEND_TIME 정각에 실행 (배치 1회 호출이라 수 초 내 완료)
    schedule.every().day.at(SEND_TIME).do(run_daily_briefing)

    # 다음 실행 시간 표시
    next_run = schedule.next_run()
    if next_run:
        print(f"   다음 실행: {next_run}")

    while True:
        schedule.run_pending()
        time.sleep(30)


def main():
    parser = argparse.ArgumentParser(
        description="🤖 AI 뉴스 데일리 디스코드 봇",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
예시:
  python main.py              매일 자동 실행 (스케줄러)
  python main.py --now        지금 바로 실행
  python main.py --dry-run    수집 & 요약만 (전송 X)
  python main.py --bot        대화형 봇 모드 (!ask 질문)
  python main.py --test       디스코드 연결 테스트
        """
    )
    parser.add_argument("--now", action="store_true", help="즉시 실행")
    parser.add_argument("--dry-run", action="store_true", help="수집 & 요약만 (전송하지 않음)")
    parser.add_argument("--test", action="store_true", help="디스코드 테스트 메시지 전송")
    parser.add_argument("--bot", action="store_true", help="대화형 봇 모드 (!ask 질문)")

    args = parser.parse_args()

    # 설정 상태 출력
    print("\n🤖 AI 뉴스 데일리 디스코드 봇")
    print(f"   Discord Webhook: {'✅ 설정됨' if DISCORD_WEBHOOK_URL else '❌ 미설정'}")
    print(f"   Gemini API Key:  {'✅ 설정됨' if GEMINI_API_KEY else '⚠️  미설정 (요약 비활성)'}")
    print(f"   전송 시간:       {SEND_TIME} KST")
    print(f"   최대 기사 수:    {MAX_ARTICLES}개\n")

    if args.test:
        send_test_message()
    elif args.bot:
        from discord_bot import run_bot
        run_bot()
    elif args.now or args.dry_run:
        run_daily_briefing(dry_run=args.dry_run)
    else:
        run_scheduler()


if __name__ == "__main__":
    main()
