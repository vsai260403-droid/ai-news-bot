"""
AI 뉴스 데일리 디스코드 봇 — 대화형 봇 (질의응답)
!ask [질문] 으로 Gemini에게 질문하고 답변을 받을 수 있습니다.
"""

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


async def handle_ask(message: discord.Message, question: str):
    """!ask 명령어 처리"""
    client = _get_gemini_client()
    if not client:
        await message.reply("⚠️ Gemini API Key가 설정되지 않았습니다.")
        return

    # 타이핑 표시
    async with message.channel.typing():
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
                # 디스코드 메시지 길이 제한 (2000자)
                if len(answer) > 1900:
                    answer = answer[:1900] + "\n\n...(답변이 잘렸습니다)"
                await message.reply(f"🤖 **AI 답변**\n\n{answer}")
            else:
                await message.reply("⚠️ AI 응답이 비어있습니다. 다시 시도해주세요.")
        except Exception as e:
            err = str(e)[:200]
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

    print("\n🤖 AI 뉴스 봇 — 대화 모드 시작")
    print(f"   Gemini Model: {GEMINI_MODEL}")
    print(f"   Gemini API Key: {'✅' if GEMINI_API_KEY else '❌'}\n")
    bot.run(DISCORD_BOT_TOKEN)


if __name__ == "__main__":
    run_bot()
