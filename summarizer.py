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


def classify_and_summarize(title: str, description: str, client) -> tuple[bool, str]:
    """
    기사가 기술/기능 기사인지 LLM이 직접 판단하고, 맞으면 한국어 요약까지 반환.
    Returns:
        (is_tech: bool, summary: str)
        할당량 초과로 API 호출 불가 시 (None, "") 반환 → 호출자가 서킷 브레이커 처리
    """
    clean_desc = _strip_html(description)

    prompt = f"""다음 기사를 읽고 두 가지를 판단해줘.

[판단 기준]
- TECH: AI 모델 출시, 새로운 기능, 연구 결과, 기술적 방법론, 제품 업데이트, 벤치마크 등
- BUSINESS: 투자 유치, M&A/인수합병, 기업 인사(CEO 교체·감원), 재무 결과, 파트너십 계약 등

[출력 형식 — 반드시 이 형식만 사용]
첫 줄: TECH 또는 BUSINESS (다른 단어 쓰지 말 것)
TECH일 경우 둘째 줄부터: 한국어 2~3문장 요약
BUSINESS일 경우: 첫 줄만 출력

제목: {title}
내용: {clean_desc[:2000]}"""

    for attempt in range(2):  # 최대 2회 시도 (RPM 일시 초과 대비)
        try:
            response = client.models.generate_content(
                model="gemini-2.0-flash",
                contents=prompt,
                config={
                    "system_instruction": SUMMARY_SYSTEM_PROMPT,
                    "temperature": 0.1,
                },
            )
            if not (response and response.text):
                return True, ""

            lines = response.text.strip().splitlines()
            verdict = lines[0].strip().upper()
            if verdict == "BUSINESS":
                return False, ""
            else:
                summary = "\n".join(lines[1:]).strip() if len(lines) > 1 else ""
                return True, summary
        except Exception as e:
            err_str = str(e)
            if "429" in err_str:
                if attempt == 0:
                    print(f"  ⏳ Rate limit, 15초 후 1회 재시도... ({title[:30]})")
                    time.sleep(15)
                else:
                    # 2회 연속 429 → 일일 할당량 초과 가능성, 서킷 브레이커 신호
                    print(f"  🚫 할당량 초과 감지 — 이후 요약 중단 ({title[:30]})")
                    return None, ""
            else:
                print(f"  ❌ API 오류 ({title[:30]}): {err_str[:100]}")
                return True, ""
    return True, ""


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

    print(f"\n🤖 {len(articles)}개 기사 LLM 분류 + 요약 중...")

    client = _create_client()
    if not client:
        print("  ⚠️  GEMINI_API_KEY가 없어 요약을 건너뜁니다.")
        for art in articles:
            art["ai_summary"] = ""
        return articles

    tech_articles = []
    api_failed_count = 0
    consecutive_fails = 0  # 연속 API 실패 카운터

    for i, art in enumerate(articles):
        print(f"  [{i + 1}/{len(articles)}] {art['title'][:50]}...")

        # 연속 3회 API 실패 → 할당량 소진으로 판단, 남은 기사 스킵
        if consecutive_fails >= 3:
            api_failed_count += 1
            print(f"  ⏭️  [할당량 소진, 스킵] {art['title'][:50]}")
            continue

        is_tech, summary = classify_and_summarize(art["title"], art["summary"], client)

        if is_tech is None:
            api_failed_count += 1
            consecutive_fails += 1
            print(f"  ⏭️  [API 실패, 제외] {art['title'][:50]}")
        elif not is_tech:
            consecutive_fails = 0  # 성공했으므로 리셋
            print(f"  ⏭️  [비즈니스 뉴스 제외] {art['title'][:50]}")
        else:
            consecutive_fails = 0
            art["ai_summary"] = summary
            tech_articles.append(art)

        if i < len(articles) - 1 and consecutive_fails < 3:
            time.sleep(5)

    excluded_biz = len(articles) - len(tech_articles) - api_failed_count
    summarized_count = sum(1 for a in tech_articles if a.get("ai_summary"))
    print(f"  ✅ {summarized_count}/{len(tech_articles)}개 요약 완료 "
          f"(비즈니스 {excluded_biz}개 제외, API 실패 {api_failed_count}개 제외)")

    return tech_articles


if __name__ == "__main__":
    # 단독 테스트
    client = _create_client()
    if client:
        is_tech, summary = classify_and_summarize(
            "OpenAI releases GPT-5 with revolutionary reasoning capabilities",
            "OpenAI has announced the release of GPT-5, featuring significant improvements in reasoning, "
            "multimodal understanding, and code generation. The new model demonstrates near-human performance "
            "on complex mathematical and scientific benchmarks.",
            client,
        )
        print(f"분류: {'TECH' if is_tech else 'BUSINESS'}")
        print(f"요약: {summary}")
    else:
        print("GEMINI_API_KEY가 설정되지 않았습니다.")
