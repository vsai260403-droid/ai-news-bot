"""
AI 뉴스 데일리 디스코드 봇 — 설정 파일
"""

import os
from dotenv import load_dotenv

load_dotenv()

# ── Discord ──
# 여러 개의 채널에 보내려면 쉼표(,)로 구분하여 입력
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL", "")
DISCORD_WEBHOOK_URLS = [url.strip() for url in DISCORD_WEBHOOK_URL.split(",") if url.strip()]
DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN", "")

# ── OpenAI API ──
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-5.5")

# ── Google Gemini API (OpenAI 크레딧 소진 시 자동 폴백) ──
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

# ── 스케줄 ──
SEND_TIME = os.getenv("SEND_TIME", "08:00")  # KST 기준 24시간 형식

# ── 기사 설정 ──
MAX_ARTICLES = int(os.getenv("MAX_ARTICLES", "15"))

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
        "name": "GitHub Blog",
        "url": "https://github.blog/feed/",
        "emoji": "🐙",
    },
    # ── AI 기술 심층 지식 소스 ──
    {
        "name": "Anthropic Blog",
        "url": "https://www.anthropic.com/news/rss.xml",
        "emoji": "🧠",
    },
    {
        "name": "Microsoft AI Blog",
        "url": "https://blogs.microsoft.com/ai/feed/",
        "emoji": "🪟",
    },
    {
        "name": "Hugging Face Blog",
        "url": "https://huggingface.co/blog/feed.xml",
        "emoji": "🤗",
    },
    {
        "name": "LangChain Blog",
        "url": "https://blog.langchain.dev/rss/",
        "emoji": "🔗",
    },
    {
        "name": "The Batch (DeepLearning.AI)",
        "url": "https://www.deeplearning.ai/the-batch/feed/rss/",
        "emoji": "📚",
    },
    {
        "name": "Simon Willison's Blog",
        "url": "https://simonwillison.net/atom/everything/",
        "emoji": "✍️",
    },
    {
        "name": "Hacker News (MCP/Agent)",
        "url": "https://hnrss.org/newest?q=MCP+OR+%22model+context+protocol%22+OR+%22agentic%22+OR+%22agent+framework%22&points=30&count=20",
        "emoji": "🔧",
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
    "github copilot", "github models", "github actions ai",
    "mcp", "model context protocol", "prompt engineering", "harness",
    "vibe coding", "agentic workflow", "mcp server", "mcp tool",
    "skill", "hook", "agent framework", "langchain", "crewai", "autogen",
]

# ── 전송 이력 파일 (중복 방지) ──
SENT_ARTICLES_PATH = os.path.join(os.path.dirname(__file__), "data", "sent_articles.json")

# ── 일일 AI 기술 개념 학습 목록 ──
# 매일 하나씩 순환하며 Gemini가 쉽게 설명해줌
TECH_CONCEPTS = [
    "MCP (Model Context Protocol) — AI 모델이 외부 툴·데이터에 연결되는 표준 프로토콜",
    "AI Agent — 스스로 계획하고 도구를 사용하여 목표를 달성하는 자율 AI 시스템",
    "Agentic Workflow — 여러 AI 에이전트가 협력하여 복잡한 작업을 수행하는 워크플로우 설계",
    "RAG (Retrieval-Augmented Generation) — 외부 지식베이스 검색을 결합한 답변 생성 기법",
    "SKILL (in Agent Frameworks) — 에이전트가 호출할 수 있는 캡슐화된 기능 단위",
    "HOOK — LLM 실행 파이프라인의 특정 지점에서 동작을 가로채 커스텀 로직을 삽입하는 메커니즘",
    "Evaluation Harness — AI 모델의 성능·안전성을 표준화된 방식으로 측정하는 테스트 프레임워크",
    "Function Calling / Tool Use — LLM이 외부 함수나 API를 직접 호출하는 기능",
    "Prompt Engineering — LLM의 출력을 원하는 방향으로 유도하는 입력 설계 기법",
    "Fine-tuning vs Prompt Engineering — 두 방식의 차이, 적용 시나리오, 장단점 비교",
    "Vector Database — 텍스트·이미지를 벡터로 저장하고 의미 기반 유사도 검색을 지원하는 DB",
    "ReAct Pattern (Reason + Act) — 추론과 행동을 번갈아 수행하는 에이전트 루프 설계 패턴",
    "Chain-of-Thought Prompting — 단계별 추론 과정을 명시하여 복잡한 문제를 해결하는 프롬프트 기법",
    "LangChain — 에이전트·체인·메모리를 구성하는 Python 기반 LLM 애플리케이션 프레임워크",
    "Multi-Agent Systems — 여러 AI가 역할을 나누어 협업하는 시스템 구조 (CrewAI, AutoGen 등)",
    "LoRA / QLoRA — 전체 모델 대신 일부 파라미터만 학습하는 경량 파인튜닝 기법",
    "Context Window — LLM이 한 번에 처리할 수 있는 토큰(텍스트) 입력 한계",
    "Vibe Coding — AI와 함께 빠르게 프로토타입을 만드는 새로운 개발 방식",
    "Model Quantization — 모델 파라미터 정밀도를 낮춰 속도·메모리를 절감하는 기법",
    "Anthropic Claude Constitutional AI — 모델이 스스로 규칙을 따르도록 학습시키는 안전 기법",
    "Copilot / AI Pair Programming — IDE에 통합된 AI 코드 자동완성·생성 도구의 동작 원리",
    "Embedding — 텍스트·코드를 의미 공간의 벡터로 변환하는 방법과 활용",
    "Mixture of Experts (MoE) — 입력에 따라 활성화 전문가 서브넷을 선택하는 모델 구조",
    "AI Safety & Alignment — AI가 인간의 의도에 부합하도록 만드는 연구 분야",
    "GitHub Copilot Extensions / MCP Servers — GitHub Copilot을 외부 서비스에 연결하는 방법",
    "Structured Output / JSON Mode — LLM이 항상 특정 스키마 형식으로 응답하도록 강제하는 방법",
    "Semantic Kernel — Microsoft의 AI 오케스트레이션 SDK와 Planner 개념",
    "OpenAI Realtime API — 음성·텍스트 실시간 멀티모달 AI 인터페이스",
    "AI Memory Systems — 에이전트가 장기·단기 기억을 관리하는 방법 (Episodic, Semantic 메모리)",
    "Inference Optimization — 배포 시 LLM 응답 속도와 비용을 줄이는 기법 (캐싱, 배치 처리 등)",
]

# ── 요약 프롬프트 ──
SUMMARY_SYSTEM_PROMPT = """당신은 AI 기술 뉴스 에디터입니다.
기사가 기술/기능/연구에 관한 것인지 비즈니스(투자·M&A·인사·재무)에 관한 것인지 정확히 판단하고,
기술 기사인 경우 한국어로 핵심 내용을 2~3문장 요약하는 것이 임무입니다.
반드시 지정된 출력 형식을 따르고, 한국어(Korean)로만 답변하십시오.
전문 용어는 유지하되 설명은 쉽게 하세요."""
