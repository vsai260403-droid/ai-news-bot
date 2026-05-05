"""
AI 뉴스 데일리 디스코드 봇 — RSS 뉴스 수집기
"""

import json
import os
import time
from datetime import datetime, timedelta, timezone
from typing import Optional

import feedparser
import requests

from config import AI_KEYWORDS, RSS_FEEDS, SENT_ARTICLES_PATH, SENT_TITLES_PATH


def load_recent_titles(days: int = 3) -> list[str]:
    """최근 N일치 전송된 기사 제목 목록 반환 (주제 중복 방지용)"""
    if not os.path.exists(SENT_TITLES_PATH):
        return []
    try:
        with open(SENT_TITLES_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, IOError):
        return []
    cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
    return [entry["title"] for entry in data if entry.get("ts", "") > cutoff]


def save_sent_titles(articles: list[dict]):
    """전송된 기사 제목을 누적 저장 (30일치 유지)"""
    existing = []
    if os.path.exists(SENT_TITLES_PATH):
        try:
            with open(SENT_TITLES_PATH, "r", encoding="utf-8") as f:
                existing = json.load(f)
        except (json.JSONDecodeError, IOError):
            existing = []
    cutoff = (datetime.now(timezone.utc) - timedelta(days=30)).isoformat()
    existing = [e for e in existing if e.get("ts", "") > cutoff]
    now_iso = datetime.now(timezone.utc).isoformat()
    for art in articles:
        existing.append({"title": art["title"], "ts": now_iso})
    _ensure_data_dir()
    with open(SENT_TITLES_PATH, "w", encoding="utf-8") as f:
        json.dump(existing, f, ensure_ascii=False, indent=2)


def _ensure_data_dir():
    """data 디렉토리가 없으면 생성"""
    data_dir = os.path.dirname(SENT_ARTICLES_PATH)
    os.makedirs(data_dir, exist_ok=True)


def _load_sent_articles() -> dict:
    """이미 전송한 기사 목록 로드"""
    _ensure_data_dir()
    if os.path.exists(SENT_ARTICLES_PATH):
        try:
            with open(SENT_ARTICLES_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {}
    return {}


def save_sent_articles(sent: dict):
    """전송한 기사 목록 저장"""
    _ensure_data_dir()
    with open(SENT_ARTICLES_PATH, "w", encoding="utf-8") as f:
        json.dump(sent, f, ensure_ascii=False, indent=2)


def _cleanup_old_entries(sent: dict, days: int = 7) -> dict:
    """N일 이상 된 전송 이력 정리 (파일 비대화 방지)"""
    cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
    return {url: ts for url, ts in sent.items() if ts > cutoff}


def _is_ai_related(title: str, summary: str) -> bool:
    """제목 또는 요약에 AI 키워드가 포함되어 있는지 확인"""
    text = (title + " " + summary).lower()
    return any(kw in text for kw in AI_KEYWORDS)


def _parse_published_date(entry) -> Optional[datetime]:
    """RSS 엔트리의 발행일을 datetime으로 변환"""
    if hasattr(entry, "published_parsed") and entry.published_parsed:
        return datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
    if hasattr(entry, "updated_parsed") and entry.updated_parsed:
        return datetime(*entry.updated_parsed[:6], tzinfo=timezone.utc)
    return None


def fetch_articles(hours: int = 24) -> list[dict]:
    """
    모든 RSS 소스에서 최근 N시간 이내의 AI 관련 기사를 수집.
    
    Returns:
        정렬된 기사 리스트. 각 기사는 dict:
        {
            "title": str,
            "url": str,
            "summary": str,       # RSS에서 제공하는 짧은 설명
            "source_name": str,
            "source_emoji": str,
            "published": datetime,
        }
    """
    cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours)
    sent_articles = _load_sent_articles()
    sent_articles = _cleanup_old_entries(sent_articles)

    all_articles = []
    seen_urls = set()

    for feed_info in RSS_FEEDS:
        source_name = feed_info["name"]
        feed_url = feed_info["url"]
        emoji = feed_info["emoji"]

        print(f"  📡 [{source_name}] 수집 중...")

        try:
            resp = requests.get(
                feed_url,
                headers={"User-Agent": "Mozilla/5.0 (compatible; AINewsBot/1.0; RSS Reader)"},
                timeout=15,
            )
            resp.raise_for_status()
            feed = feedparser.parse(resp.content)
        except requests.RequestException as e:
            print(f"  ⚠️  [{source_name}] 피드 요청 실패: {e}")
            continue
        except Exception as e:
            print(f"  ⚠️  [{source_name}] 피드 파싱 실패: {e}")
            continue

        if feed.bozo and not feed.entries:
            print(f"  ⚠️  [{source_name}] 피드 파싱 오류: {getattr(feed, 'bozo_exception', 'unknown')}")
            continue

        for entry in feed.entries:
            url = getattr(entry, "link", "")
            title = getattr(entry, "title", "")
            summary = getattr(entry, "summary", "")

            if not url or not title:
                continue

            # 중복 체크 (URL 기반)
            if url in seen_urls or url in sent_articles:
                continue

            # 발행일 체크
            published = _parse_published_date(entry)
            if published and published < cutoff_time:
                continue

            # AI 관련 키워드 필터 (AI 전용 피드는 스킵)
            is_ai_dedicated = any(
                kw in source_name.lower()
                for kw in ["ai", "openai", "google ai"]
            )
            if not is_ai_dedicated and not _is_ai_related(title, summary):
                continue

            seen_urls.add(url)
            all_articles.append({
                "title": title.strip(),
                "url": url.strip(),
                "summary": summary.strip()[:500],  # 요약은 500자까지만
                "source_name": source_name,
                "source_emoji": emoji,
                "published": published or datetime.now(timezone.utc),
            })

        # RSS 서버에 부담 주지 않기 위한 딜레이
        time.sleep(0.5)

    # 최신순 정렬
    all_articles.sort(key=lambda x: x["published"], reverse=True)

    print(f"\n  ✅ 총 {len(all_articles)}개 기사 수집 완료")
    return all_articles


if __name__ == "__main__":
    # 단독 테스트
    articles = fetch_articles()
    for i, art in enumerate(articles[:10], 1):
        print(f"\n{i}. [{art['source_name']}] {art['title']}")
        print(f"   {art['url']}")
        print(f"   {art['published'].strftime('%Y-%m-%d %H:%M')}")
