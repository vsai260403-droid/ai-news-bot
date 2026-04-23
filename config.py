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
]

# ── 전송 이력 파일 (중복 방지) ──
SENT_ARTICLES_PATH = os.path.join(os.path.dirname(__file__), "data", "sent_articles.json")

# ── Gemini 요약 프롬프트 ──
SUMMARY_SYSTEM_PROMPT = """당신은 AI/기술 뉴스 전문 편집자입니다.
주어진 기사 정보를 바탕으로 핵심 내용을 한국어 2-3문장으로 간결하게 요약해주세요.
- 전문 용어는 유지하되 쉽게 풀어서 설명해주세요.
- 왜 중요한지 한마디 덧붙여주세요.
- 마크다운 서식은 사용하지 마세요."""
