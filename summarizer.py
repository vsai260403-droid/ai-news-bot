"""
AI 뉴스 데일리 디스코드 봇 — Gemini 기반 뉴스 요약기
"""

import re
import time

from google import genai

from config import GEMINI_API_KEY, SUMMARY_SYSTEM_PROMPT


def _strip_html(text: str) -> str:
    """HTML 태그 제거"""
    return re.sub(r"<[^>]+>", "", text)


def _create_client():
    """Gemini API 클라이언트 생성"""
    if not GEMINI_API_KEY:
        return None
    return genai.Client(api_key=GEMINI_API_KEY)


def summarize_article(title: str, description: str) -> str:
    """
    기사 제목과 설명을 받아 한국어 2-3줄로 요약.
    API 키가 없거나 실패 시 빈 문자열 반환.
    """
    client = _create_client()
    if not client:
        return ""

    clean_desc = _strip_html(description)
    if len(clean_desc) < 30:
        # 본문이 너무 짧으면 요약 불필요
        return ""

    prompt = f"""다음 AI/기술 기사를 한국어 2-3문장으로 요약해주세요.

제목: {title}
내용: {clean_desc[:2000]}"""

    try:
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt,
            config={
                "system_instruction": SUMMARY_SYSTEM_PROMPT,
                "temperature": 0.3,
                "max_output_tokens": 300,
            },
        )
        return response.text.strip() if response.text else ""
    except Exception as e:
        print(f"  ⚠️  요약 실패 ({title[:40]}...): {e}")
        return ""


def summarize_articles(articles: list[dict]) -> list[dict]:
    """
    기사 리스트의 각 항목에 'ai_summary' 필드를 추가.
    API rate limit 대비 각 요청 사이에 딜레이.
    """
    if not GEMINI_API_KEY:
        print("  ⚠️  GEMINI_API_KEY가 설정되지 않았습니다. 요약을 건너뜁니다.")
        for art in articles:
            art["ai_summary"] = ""
        return articles

    print(f"\n🤖 {len(articles)}개 기사 요약 중...")

    for i, art in enumerate(articles):
        print(f"  [{i + 1}/{len(articles)}] {art['title'][:50]}...")
        art["ai_summary"] = summarize_article(art["title"], art["summary"])
        # Rate limit 대비 딜레이 (Gemini Flash는 분당 15회 제한이 있을 수 있음)
        if i < len(articles) - 1:
            time.sleep(2)

    summarized_count = sum(1 for a in articles if a["ai_summary"])
    print(f"  ✅ {summarized_count}/{len(articles)}개 요약 완료")

    return articles


if __name__ == "__main__":
    # 단독 테스트
    test = summarize_article(
        "OpenAI releases GPT-5 with revolutionary reasoning capabilities",
        "OpenAI has announced the release of GPT-5, featuring significant improvements in reasoning, "
        "multimodal understanding, and code generation. The new model demonstrates near-human performance "
        "on complex mathematical and scientific benchmarks."
    )
    print(f"요약 결과: {test}")
