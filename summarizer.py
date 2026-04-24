"""
AI 뉴스 데일리 디스코드 봇 — Gemini 기반 뉴스 요약기 (배치 처리)
"""

import json
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


def _build_batch_prompt(articles: list[dict]) -> str:
    """20개 기사를 하나의 프롬프트로 구성"""
    article_list = []
    for i, art in enumerate(articles):
        clean_desc = _strip_html(art.get("summary", ""))[:500]
        article_list.append(f"[{i}] 제목: {art['title']}\n내용: {clean_desc}")

    articles_text = "\n\n".join(article_list)

    return f"""아래 기사들을 각각 읽고 분류+요약해줘.

[판단 기준]
- TECH: AI 모델 출시, 새로운 기능, 연구 결과, 기술적 방법론, 제품 업데이트, 벤치마크, 오픈소스 등
- BUSINESS: 투자 유치, M&A/인수합병, 기업 인사(CEO 교체·감원), 재무 결과, 파트너십 계약, 이벤트/컨퍼런스 티켓 홍보 등

[출력 형식 — 반드시 JSON 배열로만 출력. 다른 텍스트 없이 JSON만 출력할 것]
[
  {{"id": 0, "type": "TECH", "summary": "한국어 2~3문장 요약"}},
  {{"id": 1, "type": "BUSINESS", "summary": ""}},
  ...
]

- TECH 기사: summary에 한국어로 2~3문장 요약
- BUSINESS 기사: summary는 빈 문자열

{articles_text}"""


def summarize_articles(articles: list[dict]) -> list[dict]:
    """
    기사 리스트를 1회 API 호출로 분류+요약.
    TECH 기사만 필터링하여 ai_summary 포함해 반환.
    """
    if not GEMINI_API_KEY:
        print("  ⚠️  GEMINI_API_KEY가 설정되지 않았습니다. 요약을 건너뜁니다.")
        for art in articles:
            art["ai_summary"] = ""
        return articles

    client = _create_client()
    if not client:
        for art in articles:
            art["ai_summary"] = ""
        return articles

    print(f"\n🤖 {len(articles)}개 기사 일괄 분류 + 요약 중... (1회 API 호출)")

    prompt = _build_batch_prompt(articles)

    for attempt in range(3):
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
                print("  ⚠️  API 응답이 비어있습니다. 전체 기사를 요약 없이 전송합니다.")
                for art in articles:
                    art["ai_summary"] = ""
                return articles

            # JSON 파싱 (```json ... ``` 감싸기 대응)
            text = response.text.strip()
            if text.startswith("```"):
                text = re.sub(r"^```(?:json)?\s*", "", text)
                text = re.sub(r"\s*```$", "", text)

            results = json.loads(text)
            break
        except json.JSONDecodeError as e:
            print(f"  ⚠️  JSON 파싱 실패 (시도 {attempt + 1}/3): {str(e)[:80]}")
            if attempt < 2:
                time.sleep(5)
            else:
                print("  ⚠️  JSON 파싱 최종 실패. 전체 기사를 요약 없이 전송합니다.")
                for art in articles:
                    art["ai_summary"] = ""
                return articles
        except Exception as e:
            err_str = str(e)
            if "429" in err_str:
                # 에러 메시지에서 RPM/RPD 구분
                err_lower = err_str.lower()
                if "per_minute" in err_lower or "rpm" in err_lower or "minute" in err_lower:
                    limit_type = "⏱️ 분당 한도(RPM) 초과"
                elif "per_day" in err_lower or "rpd" in err_lower or "daily" in err_lower:
                    limit_type = "📅 일일 한도(RPD) 초과"
                else:
                    limit_type = "🚫 API 할당량 초과"

                if attempt < 2:
                    wait = (attempt + 1) * 15
                    print(f"  ⏳ {limit_type}, {wait}초 후 재시도... (시도 {attempt + 1}/3)")
                    time.sleep(wait)
                else:
                    print(f"  ❌ {limit_type} — 3회 재시도 실패. 요약 없이 전송합니다.")
                    for art in articles:
                        art["ai_summary"] = ""
                    return articles
            else:
                print(f"  ❌ API 오류: {err_str[:150]}")
                for art in articles:
                    art["ai_summary"] = ""
                return articles

    # 결과 매핑
    result_map = {r["id"]: r for r in results}
    tech_articles = []

    for i, art in enumerate(articles):
        r = result_map.get(i, {})
        verdict = r.get("type", "TECH").upper()
        summary = r.get("summary", "")

        if verdict == "BUSINESS":
            print(f"  ⏭️  [비즈니스 뉴스 제외] {art['title'][:50]}")
        else:
            art["ai_summary"] = summary
            tech_articles.append(art)

    excluded = len(articles) - len(tech_articles)
    summarized = sum(1 for a in tech_articles if a.get("ai_summary"))
    print(f"  ✅ {summarized}/{len(tech_articles)}개 요약 완료 (비즈니스 {excluded}개 제외)")

    return tech_articles


if __name__ == "__main__":
    # 단독 테스트
    test_articles = [
        {"title": "OpenAI releases GPT-5", "summary": "New reasoning model with improved benchmarks."},
        {"title": "Startup raises $50M", "summary": "AI startup raises Series B funding."},
    ]
    result = summarize_articles(test_articles)
    for art in result:
        print(f"  [{art['title']}] {art.get('ai_summary', '')}")
