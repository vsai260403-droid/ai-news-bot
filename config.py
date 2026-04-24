"""
AI 뉴스 데일리 디스코드 봇 — 설정 파일
"""

import os
from dotenv import load_dotenv

load_dotenv()

# ── Discord ──
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL", "")

# ── Gemini API ──
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

# ── 스케줄 ──
SEND_TIME = os.getenv("SEND_TIME", "08:00")  # KST 기준 24시간 형식

# ── 기사 설정 ──
MAX_ARTICLES = int(os.getenv("MAX_ARTICLES", "10"))

# ── RSS 피드 소스 ──
RSS_FEEDS = [
    {
        "name": "MIT Technology Review",
        "url": "https://www.technologyreview.com/topic/artificial-intelligence/feed/",
        "emoji": "🎓",
    },
    {
        "name": "TechCrunch AI",
        "url": "https://techcrunch.com/category/artificial-intelligence/feed/",
        "emoji": "💻",
    },
    {
        "name": "Hacker News (AI)",
        "url": "https://hnrss.org/newest?q=AI+OR+LLM+OR+GPT+OR+%22machine+learning%22&points=50&count=30",
        "emoji": "🔶",
    },
    {
        "name": "The Verge (AI)",
        "url": "https://www.theverge.com/rss/ai-artificial-intelligence/index.xml",
        "emoji": "📱",
    },
    {
        "name": "Ars Technica",
        "url": "https://feeds.arstechnica.com/arstechnica/technology-lab",
        "emoji": "🔬",
    },
    {
        "name": "OpenAI Blog",
        "url": "https://openai.com/blog/rss.xml",
        "emoji": "🤖",
    },
    {
        "name": "Google AI Blog",
        "url": "https://blog.google/technology/ai/rss/",
        "emoji": "🔵",
    },
    {
        "name": "Anthropic Blog",
        "url": "https://www.anthropic.com/rss.xml",
        "emoji": "🟤",
    },
    {
        "name": "GitHub Blog",
        "url": "https://github.blog/feed/",
        "emoji": "🐙",
    },
]

# ── 비즈니스/기업 뉴스 제외 키워드 ──
# 기술/기능 기사가 아닌 투자·M&A·인사 뉴스를 걸러냄
BUSINESS_EXCLUDE_KEYWORDS = [
    # 투자·자금
    "raises", "raised", "funding", "investment", "investors", "valuation",
    "series a", "series b", "series c", "seed round", "venture",
    # M&A·파트너십
    "acquisition", "acquires", "acquired", "merger", "merges", "acquired by",
    "partnership", "partners with", "deal worth", "signs deal",
    # 상장·재무
    "ipo", "goes public", "stock", "shares", "revenue", "earnings", "profit",
    "quarterly results", "annual report",
    # 인사·조직
    "layoffs", "layoff", "fired", "hires", "new ceo", "new chief", "appointed",
    "appoints", "steps down", "resigns", "joins as",
]

# ── AI 관련 키워드 (필터링용) ──
# Hacker News, Ars Technica 등 범용 피드에서 AI 관련 기사만 걸러내기 위한 키워드
AI_KEYWORDS = [
    "ai", "artificial intelligence", "machine learning", "deep learning",
    "llm", "large language model", "gpt", "gemini", "claude", "openai",
    "anthropic", "google ai", "deepmind", "neural network", "transformer",
    "chatbot", "generative ai", "gen ai", "diffusion", "stable diffusion",
    "midjourney", "copilot", "foundation model", "agi", "reasoning model",
    "agent", "agentic", "rag", "retrieval augmented", "fine-tuning",
    "multimodal", "computer vision", "nlp", "natural language",
    "reinforcement learning", "hugging face", "meta ai", "mistral",
    "llama", "sora", "인공지능", "머신러닝", "딥러닝",
    "github copilot", "github models", "github actions ai",
]

# ── 전송 이력 파일 (중복 방지) ──
SENT_ARTICLES_PATH = os.path.join(os.path.dirname(__file__), "data", "sent_articles.json")

# ── Gemini 요약 프롬프트 ──
SUMMARY_SYSTEM_PROMPT = """당신은 AI 기술 뉴스 에디터입니다. 
영문 기사를 읽고 한국어로 핵심 내용을 2~3문장 요약하는 것이 임무입니다.
반드시 한국어(Korean)로만 답변하십시오. 전문 용어는 유지하되 설명은 쉽게 하세요."""
