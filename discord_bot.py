"""
AI 뉴스 데일리 디스코드 봇 — 대화형 봇 (질의응답)
!ask [질문] 으로 Gemini에게 질문하고 답변을 받을 수 있습니다.
"""

import asyncio
import discord
from google import genai

from config import DISCORD_BOT_TOKEN, GEMINI_API_KEY, GEMINI_MODEL

# Gemini 클라이언트
_gemini_client = None


def _get_gemini_client():
    global _gemini_client
    if _gemini_client is None and GEMINI_API_KEY:
        _gemini_client = genai.Client(api_key=GEMINI_API_KEY)
    return _gemini_client


SYSTEM_PROMPT = """당신은 AI/기술 분야 전문 어시스턴트입니다.
사용자의 질문에 한국어로 정확하고 간결하게 답변하세요.
기술 용어는 유지하되 설명은 쉽게 하세요.
답변은 디스코드 메시지로 보내지므로 2000자 이내로 작성하세요."""


WELCOME_MESSAGE = """
📌 **AI 뉴스 데일리 봇 가이드**
━━━━━━━━━━━━━━━━━━━━

🗞️ **자동 뉴스 브리핑**
매일 아침 **8시(KST)** 에 AI/기술 뉴스 TOP 10을 자동으로 전송합니다.
• 9개 글로벌 소스에서 수집 (TechCrunch, The Verge, OpenAI, Google AI 등)
• AI가 중요도 순으로 선별하고 한국어로 요약
• 비즈니스 뉴스·중복 기사는 자동 제외

💬 **AI 질의응답**
`!ask` 명령어로 AI에게 질문할 수 있습니다.

> `!ask GPT-5.5가 뭐야?`
> `!ask 트랜스포머 아키텍처 쉽게 설명해줘`
> `!ask 오늘 AI 뉴스 트렌드 정리해줘`

📋 **명령어 목록**
• `!ask [질문]` — AI에게 질문하기
• `!help` — 이 안내 메시지 보기

━━━━━━━━━━━━━━━━━━━━
🤖 Powered by Gemini AI
""".strip()


async def handle_ask(message: discord.Message, question: str):
    """!ask 명령어 처리"""
    client = _get_gemini_client()
    if not client:
        await message.reply("⚠️ Gemini API Key가 설정되지 않았습니다.")
        return

    # 타이핑 표시
    async with message.channel.typing():
        last_err = None
        for attempt in range(3):
            try:
                response = client.models.generate_content(
                    model=GEMINI_MODEL,
                    contents=question,
                    config={
                        "system_instruction": SYSTEM_PROMPT,
                        "temperature": 0.7,
                    },
                )
                if response and response.text:
                    answer = response.text.strip()
                    if len(answer) > 1900:
                        answer = answer[:1900] + "\n\n...(답변이 잘렸습니다)"
                    await message.reply(f"🤖 **AI 답변**\n\n{answer}")
                else:
                    await message.reply("⚠️ AI 응답이 비어있습니다. 다시 시도해주세요.")
                return
            except Exception as e:
                last_err = str(e)
                if "503" in last_err or "UNAVAILABLE" in last_err:
                    await asyncio.sleep(2 * (attempt + 1))
                    continue
                break
        err = last_err[:200] if last_err else "알 수 없는 오류"
        await message.reply(f"❌ API 오류: {err}")


def run_bot():
    """디스코드 봇 실행"""
    if not DISCORD_BOT_TOKEN:
        print("❌ DISCORD_BOT_TOKEN이 설정되지 않았습니다.")
        print("   Discord Developer Portal에서 봇을 만들고 토큰을 .env에 추가하세요.")
        return

    intents = discord.Intents.default()
    intents.message_content = True
    bot = discord.Client(intents=intents)

    @bot.event
    async def on_ready():
        print(f"🤖 디스코드 봇 온라인: {bot.user}")
        print(f"   !ask [질문] 으로 AI에게 질문할 수 있습니다.")

    @bot.event
    async def on_message(message: discord.Message):
        # 봇 자신의 메시지 무시
        if message.author == bot.user:
            return

        if message.content.startswith("!ask "):
            question = message.content[5:].strip()
            if not question:
                await message.reply("💡 사용법: `!ask AI 뉴스 트렌드 알려줘`")
                return
            await handle_ask(message, question)

        elif message.content == "!help":
            await message.channel.send(WELCOME_MESSAGE)

        elif message.content == "!pin":
            # 관리자만 고정 메시지 가능
            if message.author.guild_permissions.manage_messages:
                msg = await message.channel.send(WELCOME_MESSAGE)
                await msg.pin()
                await message.delete()
            else:
                await message.reply("⚠️ 메시지 고정은 관리자만 가능합니다.")

    print("\n🤖 AI 뉴스 봇 — 대화 모드 시작")
    print(f"   Gemini Model: {GEMINI_MODEL}")
    print(f"   Gemini API Key: {'✅' if GEMINI_API_KEY else '❌'}\n")
    bot.run(DISCORD_BOT_TOKEN)


if __name__ == "__main__":
    run_bot()
