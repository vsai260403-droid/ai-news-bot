"""
AI 뉴스 데일리 디스코드 봇 — GPT 기반 뉴스 요약기 (배치 처리)
"""

import json
import re
import time

from openai import OpenAI

from config import OPENAI_API_KEY, OPENAI_MODEL, GEMINI_API_KEY, GEMINI_MODEL, SUMMARY_SYSTEM_PROMPT, TECH_CONCEPTS, USED_CONCEPTS_PATH


def _strip_html(text: str) -> str:
    """HTML 태그 제거"""
    return re.sub(r"<[^>]+>", "", text)


def _parse_json_response(raw_text: str) -> list:
    """API 응답 텍스트에서 JSON 배열 파싱 (```json 감싸기 대응)"""
    text = raw_text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    return json.loads(text)


def _call_with_retry(client, model: str, prompt: str, provider_name: str):
    """
    최대 3회 재시도로 API 호출.
    Returns: (results_list | None, fallback_needed: bool)
      - results_list: 성공 시 파싱된 JSON 리스트
      - fallback_needed: True면 다음 provider로 넘겨야 함
    """
    for attempt in range(3):
        try:
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": SUMMARY_SYSTEM_PROMPT},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.1,
            )
            raw_text = response.choices[0].message.content if response.choices else None
            if not raw_text:
                print(f"  ⚠️  [{provider_name}] API 응답이 비어있습니다.")
                return None, False

            results = _parse_json_response(raw_text)
            print(f"  ✅ [{provider_name}] API 호출 성공")
            return results, False

        except json.JSONDecodeError as e:
            print(f"  ⚠️  [{provider_name}] JSON 파싱 실패 (시도 {attempt + 1}/3): {str(e)[:80]}")
            if attempt < 2:
                time.sleep(5)
            else:
                print(f"  ⚠️  [{provider_name}] JSON 파싱 최종 실패.")
                return None, False

        except Exception as e:
            err_str = str(e)
            if "429" in err_str:
                print(f"  📋 [{provider_name}] 에러 원문: {err_str[:300]}")
                err_lower = err_str.lower()

                if "insufficient_quota" in err_lower:
                    print(f"  ❌ [{provider_name}] 💳 크레딧 소진 → 다음 provider로 전환합니다.")
                    return None, True  # fallback 필요

                if "per_day" in err_lower or "rpd" in err_lower or "daily" in err_lower:
                    limit_type = "📅 일일 한도(RPD) 초과"
                elif "per_minute" in err_lower or "rpm" in err_lower or "minute" in err_lower:
                    limit_type = "⏱️ 분당 한도(RPM) 초과"
                else:
                    limit_type = "🚫 API 할당량 초과"

                if attempt < 2:
                    wait = (attempt + 1) * 30
                    print(f"  ⏳ [{provider_name}] {limit_type}, {wait}초 후 재시도... (시도 {attempt + 1}/3)")
                    time.sleep(wait)
                else:
                    print(f"  ❌ [{provider_name}] {limit_type} — 3회 재시도 실패.")
                    return None, False
            else:
                print(f"  ❌ [{provider_name}] API 오류: {err_str[:150]} → 다음 provider로 전환")
                return None, True  # fallback 시도

            # 5xx 서버 오류: 재시도 후 fallback
            is_5xx = any(code in err_str for code in ["503", "502", "500", "504"]) or \
                     any(kw in err_str.lower() for kw in ["service unavailable", "overloaded", "server error"])
            if is_5xx:
                if attempt < 2:
                    wait = (attempt + 1) * 20
                    print(f"  ⏳ [{provider_name}] 서버 오류(5xx), {wait}초 후 재시도... (시도 {attempt + 1}/3)")
                    time.sleep(wait)
                else:
                    print(f"  ❌ [{provider_name}] 서버 오류 3회 재시도 실패 → 다음 provider로 전환")
                    return None, True
            else:
                print(f"  ❌ [{provider_name}] API 오류: {err_str[:150]} → 다음 provider로 전환")
                return None, True  # fallback 시도

    return None, False


def _build_batch_prompt(articles: list[dict]) -> str:
    """기사들을 하나의 프롬프트로 구성 (분류+중요도+요약)"""
    article_list = []
    for i, art in enumerate(articles):
        clean_desc = _strip_html(art.get("summary", ""))[:500]
        article_list.append(f"[{i}] 제목: {art['title']}\n내용: {clean_desc}")

    articles_text = "\n\n".join(article_list)

    return f"""아래 기사들을 각각 읽고 분류+중요도 평가+요약해줘.

[판단 기준]
- TECH: AI 모델 출시, 새로운 기능, 연구 결과, 기술적 방법론, 제품 업데이트, 벤치마크, 오픈소스 등
- BUSINESS: 투자 유치, M&A/인수합병, 기업 인사(CEO 교체·감원), 재무 결과, 파트너십 계약, 이벤트/컨퍼런스 티켓 홍보 등
- DUPLICATE: 같은 주제/사건을 다루는 기사가 여러 개 있으면, 가장 상세한 1개만 TECH/BUSINESS로 분류하고 나머지는 DUPLICATE로 표시

[중요도 점수 기준 (1~10)]
- 10: 업계 판도를 바꾸는 메이저 발표 (새 모델, 획기적 기능)
- 7~9: 주요 제품 업데이트, 중요한 연구 결과, 대규모 오픈소스 공개
- 4~6: 일반적인 기능 업데이트, 흥미로운 프로젝트, 분석 기사
- 1~3: 사소한 업데이트, 의견 기사, 간접적 AI 관련

[출력 형식 — 반드시 JSON 배열로만 출력. 다른 텍스트 없이 JSON만 출력할 것]
[
  {{"id": 0, "type": "TECH", "score": 9, "summary": "한국어 2~3문장 요약"}},
  {{"id": 1, "type": "BUSINESS", "score": 0, "summary": ""}},
  {{"id": 2, "type": "DUPLICATE", "score": 0, "summary": ""}},
  ...
]

- TECH 기사: score(1~10) + summary에 한국어로 2~3문장 요약
- BUSINESS / DUPLICATE 기사: score는 0, summary는 빈 문자열

{articles_text}"""


def summarize_articles(articles: list[dict]) -> list[dict]:
    """
    기사 리스트를 1회 API 호출로 분류+요약.
    OpenAI 우선 시도, 크레딧 소진 시 Gemini로 자동 폴백.
    TECH 기사만 필터링하여 ai_summary 포함해 반환.
    """
    print(f"\n🤖 {len(articles)}개 기사 일괄 분류 + 요약 중... (1회 API 호출)")

    # 사용할 provider 목록 구성 (순서대로 시도)
    providers = []
    if OPENAI_API_KEY:
        providers.append((
            OpenAI(api_key=OPENAI_API_KEY),
            OPENAI_MODEL,
            "OpenAI",
        ))
    if GEMINI_API_KEY:
        providers.append((
            OpenAI(
                api_key=GEMINI_API_KEY,
                base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
            ),
            "gemini-2.5-flash",
            "Gemini",
        ))

    if not providers:
        print("  ⚠️  API 키 없음 (OPENAI_API_KEY 또는 GEMINI_API_KEY). 요약을 건너뜁니다.")
        for art in articles:
            art["ai_summary"] = ""
        return articles

    prompt = _build_batch_prompt(articles)
    results = None

    for client, model, name in providers:
        print(f"  🔄 [{name}] {model} 호출 중...")
        try:
            results, fallback_needed = _call_with_retry(client, model, prompt, name)
        except Exception as e:
            print(f"  ❌ [{name}] 예상치 못한 오류: {str(e)[:150]}")
            results, fallback_needed = None, True
        if results is not None:
            break
        if not fallback_needed:
            break
        # fallback_needed=True → 다음 provider로 계속

    if results is None:
        print("  ⚠️  모든 API 호출 실패. 요약 없이 전송합니다.")
        for art in articles:
            art["ai_summary"] = ""
        return articles

    # 결과 매핑
    result_map = {r["id"]: r for r in results}
    tech_articles = []
    excluded_biz = 0
    excluded_dup = 0

    for i, art in enumerate(articles):
        r = result_map.get(i, {})
        verdict = r.get("type", "TECH").upper()
        summary = r.get("summary", "")
        score = r.get("score", 5)

        if verdict == "BUSINESS":
            excluded_biz += 1
            print(f"  \u23ed\ufe0f  [비즈니스 제외] {art['title'][:50]}")
        elif verdict == "DUPLICATE":
            excluded_dup += 1
            print(f"  \u23ed\ufe0f  [중복 제외] {art['title'][:50]}")
        else:
            art["ai_summary"] = summary
            art["importance_score"] = score
            tech_articles.append(art)

    # 중요도 순 정렬 (높은 점수가 위로)
    tech_articles.sort(key=lambda x: x.get("importance_score", 0), reverse=True)

    summarized = sum(1 for a in tech_articles if a.get("ai_summary"))
    print(f"  ✅ {summarized}/{len(tech_articles)}개 요약 완료 "
          f"(비즈니스 {excluded_biz}개, 중복 {excluded_dup}개 제외)")

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


def _load_used_concepts() -> list[str]:
    """사용된 개념 이름 목록 로드"""
    import os
    if not os.path.exists(USED_CONCEPTS_PATH):
        return []
    try:
        with open(USED_CONCEPTS_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []


def _save_used_concept(concept_short: str) -> None:
    """사용된 개념 이름을 이력 파일에 추가"""
    import os
    os.makedirs(os.path.dirname(USED_CONCEPTS_PATH), exist_ok=True)
    used = _load_used_concepts()
    if concept_short not in used:
        used.append(concept_short)
    with open(USED_CONCEPTS_PATH, "w", encoding="utf-8") as f:
        json.dump(used, f, ensure_ascii=False, indent=2)


def generate_daily_concept() -> dict | None:
    """
    오늘의 AI 기술 개념 카드를 생성.
    - 기본 30개 목록을 순서대로 소진 (미사용 항목 우선)
    - 30개 모두 사용 후엔 AI가 최신 트렌드 기반으로 새 개념을 동적 생성
    Returns: {"concept_short": str, "one_line": str, "explanation": str, "analogy": str, "use_case": str} or None
    """
    used = _load_used_concepts()

    # 기본 30개 중 아직 사용하지 않은 첫 번째 항목 선택
    concept = None
    for c in TECH_CONCEPTS:
        # 개념 식별자: 대시(—) 앞 부분 또는 전체
        short_key = c.split("—")[0].strip()
        if short_key not in used:
            concept = c
            break

    if concept:
        print(f"\n🎓 오늘의 AI 개념 생성 중 (기본 목록): [{concept}]")
    else:
        print(f"\n🎓 기본 30개 소진 — AI가 최신 트렌드 기반으로 새 개념을 동적 생성 중...")

    if concept:
        prompt = f"""당신은 AI 기술을 쉽게 가르쳐주는 전문가입니다.
오늘의 AI 기술 개념을 아래 형식대로 설명해주세요.

개념: {concept}

[출력 형식 - 반드시 JSON으로만, 다른 텍스트 없이]
{{
  "concept_short": "개념의 짧은 이름 (예: MCP, RAG, LoRA)",
  "one_line": "한 줄 정의 (30자 이내)",
  "explanation": "실무 엔지니어 관점에서 3~4문장으로 설명. 왜 중요한지, 어떻게 동작하는지 포함.",
  "analogy": "비전공자도 이해할 수 있는 현실 세계 비유 1~2문장",
  "use_case": "실제 적용 예시 1개 (구체적인 제품이나 코드 사용 사례)"
}}"""
    else:
        already_used_str = ", ".join(used[-50:])  # 최근 50개만 전달해 프롬프트 크기 제한
        prompt = f"""당신은 AI 기술을 쉽게 가르쳐주는 전문가이자 최신 AI 트렌드 연구자입니다.

아래는 이미 다룬 AI 기술 개념 목록입니다:
{already_used_str}

2024~2026년 최신 AI/ML 트렌드 중 위 목록에 없는 새로운 개념 하나를 골라 설명해주세요.
최신 논문, 모델 출시, 프레임워크 업데이트, 업계 동향을 참고하여 트렌디하고 실용적인 개념을 선택하세요.

[출력 형식 - 반드시 JSON으로만, 다른 텍스트 없이]
{{
  "concept_short": "개념의 짧은 이름 (예: KV Cache, Speculative Decoding)",
  "one_line": "한 줄 정의 (30자 이내)",
  "explanation": "실무 엔지니어 관점에서 3~4문장으로 설명. 왜 중요한지, 어떻게 동작하는지 포함.",
  "analogy": "비전공자도 이해할 수 있는 현실 세계 비유 1~2문장",
  "use_case": "실제 적용 예시 1개 (구체적인 제품이나 코드 사용 사례)"
}}"""

    providers = []
    if GEMINI_API_KEY:
        providers.append((
            OpenAI(
                api_key=GEMINI_API_KEY,
                base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
            ),
            "gemini-2.5-flash",
            "Gemini",
        ))
    if OPENAI_API_KEY:
        providers.append((
            OpenAI(api_key=OPENAI_API_KEY),
            OPENAI_MODEL,
            "OpenAI",
        ))

    for client, model, name in providers:
        try:
            response = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
            )
            raw = response.choices[0].message.content or ""
            result = _parse_json_response(raw)
            if result and isinstance(result, dict):
                concept_short = result.get("concept_short", "")
                if concept_short:
                    _save_used_concept(concept_short)
                    print(f"  ✅ [{name}] 개념 카드 생성 완료: {concept_short}")
                else:
                    print(f"  ✅ [{name}] 개념 카드 생성 완료")
            return result
        except Exception as e:
            print(f"  ⚠️  [{name}] 개념 생성 실패: {str(e)[:100]}")
            continue

    print("  ⚠️  개념 카드 생성 실패 — 건너뜁니다.")
    return None