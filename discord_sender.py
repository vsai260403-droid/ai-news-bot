"""
AI 뉴스 데일리 디스코드 봇 — 디스코드 전송 모듈
"""

from datetime import datetime, timezone, timedelta

from discord_webhook import DiscordEmbed, DiscordWebhook

from config import DISCORD_WEBHOOK_URL


# KST 타임존
KST = timezone(timedelta(hours=9))


def _build_embeds(articles: list[dict]) -> list[DiscordEmbed]:
    """기사 목록을 Discord Embed 리스트로 변환"""
    embeds = []

    for i, art in enumerate(articles):
        emoji = art.get("source_emoji", "📰")
        source = art.get("source_name", "Unknown")

        # 요약 텍스트 구성
        description_parts = []
        if art.get("ai_summary"):
            description_parts.append(art["ai_summary"])
        description_parts.append(f"\n🔗 [원문 읽기]({art['url']})")
        description = "\n".join(description_parts)

        embed = DiscordEmbed(
            title=f"{i + 1}. {art['title'][:200]}",
            description=description[:4096],  # Discord 제한
            color=_get_source_color(source),
            url=art["url"],
        )
        embed.set_footer(text=f"{emoji} {source}")

        # 발행일
        if art.get("published"):
            pub = art["published"]
            embed.set_timestamp(pub.isoformat())

        embeds.append(embed)

    return embeds


def _get_source_color(source_name: str) -> int:
    """소스별 임베드 색상"""
    colors = {
        "MIT Technology Review": 0xE74C3C,   # 빨강
        "TechCrunch AI": 0x2ECC71,           # 초록
        "Hacker News (AI)": 0xFF6600,        # 오렌지
        "The Verge (AI)": 0x9B59B6,          # 보라
        "Ars Technica": 0x3498DB,            # 파랑
        "OpenAI Blog": 0x1ABC9C,             # 청록
        "Google AI Blog": 0x4285F4,          # 구글 블루
    }
    return colors.get(source_name, 0x95A5A6)


def send_to_discord(articles: list[dict]) -> bool:
    """
    기사 목록을 디스코드 채널에 전송.
    
    Discord Webhook은 한 번에 최대 10개의 embed만 보낼 수 있으므로,
    헤더 메시지 + 기사 임베드를 나누어 전송.
    
    Returns:
        True if 전송 성공, False otherwise.
    """
    if not DISCORD_WEBHOOK_URL:
        print("  ❌ DISCORD_WEBHOOK_URL이 설정되지 않았습니다.")
        return False

    if not articles:
        print("  ℹ️  전송할 기사가 없습니다.")
        return False

    today = datetime.now(KST).strftime("%Y년 %m월 %d일")

    try:
        # ── 헤더 메시지 ──
        header = (
            f"# 🤖 AI 뉴스 데일리 브리핑\n"
            f"**📅 {today}** • 총 {len(articles)}개 기사\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        )

        webhook = DiscordWebhook(
            url=DISCORD_WEBHOOK_URL,
            content=header,
            username="AI News Bot",
        )
        response = webhook.execute()
        if response and hasattr(response, "status_code") and response.status_code not in (200, 204):
            print(f"  ⚠️  헤더 전송 실패: {response.status_code}")

        # ── 기사 임베드 전송 (10개씩 나누어) ──
        embeds = _build_embeds(articles)
        batch_size = 10

        for batch_start in range(0, len(embeds), batch_size):
            batch = embeds[batch_start:batch_start + batch_size]

            webhook = DiscordWebhook(
                url=DISCORD_WEBHOOK_URL,
                username="AI News Bot",
            )
            for embed in batch:
                webhook.add_embed(embed)

            response = webhook.execute()
            if response and hasattr(response, "status_code") and response.status_code not in (200, 204):
                print(f"  ⚠️  기사 배치 전송 실패: {response.status_code}")
                return False

        print(f"  ✅ 디스코드 전송 완료 ({len(articles)}개 기사)")
        return True

    except Exception as e:
        print(f"  ❌ 디스코드 전송 오류: {e}")
        return False


def send_test_message() -> bool:
    """테스트 메시지 전송"""
    if not DISCORD_WEBHOOK_URL:
        print("  ❌ DISCORD_WEBHOOK_URL이 설정되지 않았습니다.")
        return False

    try:
        webhook = DiscordWebhook(
            url=DISCORD_WEBHOOK_URL,
            content="🧪 **AI 뉴스 봇 테스트** — 연결 성공!",
            username="AI News Bot",
        )
        response = webhook.execute()
        success = response and hasattr(response, "status_code") and response.status_code in (200, 204)
        if success:
            print("  ✅ 테스트 메시지 전송 성공")
        else:
            status = getattr(response, "status_code", "unknown") if response else "no response"
            print(f"  ❌ 테스트 전송 실패: {status}")
        return success
    except Exception as e:
        print(f"  ❌ 테스트 전송 오류: {e}")
        return False


if __name__ == "__main__":
    send_test_message()
