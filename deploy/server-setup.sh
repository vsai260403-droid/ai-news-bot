#!/bin/bash
# ==================================================
# AI News Bot — 서버 설치 스크립트 (git clone 방식)
# Ubuntu 22.04 / 24.04 기준
#
# 사용법:
#   curl -fsSL https://raw.githubusercontent.com/vsai260403-droid/ai-news-bot/main/deploy/server-setup.sh | sudo bash
# 또는:
#   git clone https://github.com/vsai260403-droid/ai-news-bot.git && sudo bash ai-news-bot/deploy/server-setup.sh
# ==================================================
set -e

REPO_URL="https://github.com/vsai260403-droid/ai-news-bot.git"
APP_DIR="/opt/ai-news-bot"
SERVICE_USER="${SUDO_USER:-ubuntu}"  # sudo 실행 시 원래 사용자 자동 감지

echo "=================================================="
echo "🚀 AI News Bot 서버 설치 시작"
echo "   서버 사용자: $SERVICE_USER"
echo "=================================================="

# 1. 패키지 업데이트 & Python / git 설치
echo ""
echo "📦 Step 1: 시스템 패키지 업데이트"
apt-get update -q
apt-get install -y python3 python3-pip python3-venv git

# 2. git clone (또는 pull)
echo ""
echo "📥 Step 2: 코드 다운로드 ($REPO_URL)"
if [ -d "$APP_DIR/.git" ]; then
    echo "  이미 존재하는 저장소 — git pull 실행"
    git -C "$APP_DIR" pull
else
    git clone "$REPO_URL" "$APP_DIR"
fi
mkdir -p "$APP_DIR/data"
chown -R "$SERVICE_USER":"$SERVICE_USER" "$APP_DIR"

# 3. Python 가상환경 & 의존성 설치
echo ""
echo "🐍 Step 3: Python 가상환경 구성"
sudo -u "$SERVICE_USER" python3 -m venv "$APP_DIR/venv"
sudo -u "$SERVICE_USER" "$APP_DIR/venv/bin/pip" install --quiet --upgrade pip
sudo -u "$SERVICE_USER" "$APP_DIR/venv/bin/pip" install --quiet -r "$APP_DIR/requirements.txt"

# 4. .env 파일 확인
echo ""
echo "🔑 Step 4: 환경변수 파일 확인"
if [ ! -f "$APP_DIR/.env" ]; then
    echo "  ⚠️  .env 파일이 없습니다. 템플릿을 생성합니다..."
    cat > "$APP_DIR/.env" << 'EOF'
DISCORD_WEBHOOK_URL=your_webhook_url_here
DISCORD_BOT_TOKEN=your_bot_token_here
OPENAI_API_KEY=your_openai_api_key_here
GEMINI_API_KEY=your_gemini_api_key_here
MAX_ARTICLES=10
EOF
    chown "$SERVICE_USER":"$SERVICE_USER" "$APP_DIR/.env"
    chmod 600 "$APP_DIR/.env"
    echo "  📝 $APP_DIR/.env 를 편집하고 API 키를 입력하세요:"
    echo "     nano $APP_DIR/.env"
else
    echo "  ✅ .env 파일이 이미 존재합니다."
    chmod 600 "$APP_DIR/.env"
fi

# 5. systemd 서비스 파일 설치
echo ""
echo "⚙️  Step 5: systemd 서비스 등록"

# 현재 서버 사용자명으로 서비스 파일 업데이트
sed -i "s/User=ubuntu/User=$SERVICE_USER/g" "$APP_DIR/deploy/ai-news-bot.service"
sed -i "s/User=ubuntu/User=$SERVICE_USER/g" "$APP_DIR/deploy/ai-news-daily.service"

cp "$APP_DIR/deploy/ai-news-bot.service"    /etc/systemd/system/
cp "$APP_DIR/deploy/ai-news-daily.service"  /etc/systemd/system/
cp "$APP_DIR/deploy/ai-news-daily.timer"    /etc/systemd/system/

systemctl daemon-reload

# 6. 서비스 활성화 & 시작
echo ""
echo "🟢 Step 6: 서비스 시작"

# 타이머 (매일 9시 자동 실행)
systemctl enable ai-news-daily.timer
systemctl start  ai-news-daily.timer

# 봇 (항상 켜져 있음)
systemctl enable ai-news-bot
systemctl start  ai-news-bot

# 7. 상태 확인
echo ""
echo "=================================================="
echo "✅ 설치 완료!"
echo "=================================================="
echo ""
echo "📊 상태 확인 명령어:"
echo "  systemctl status ai-news-bot           # 봇 상태"
echo "  systemctl status ai-news-daily.timer   # 타이머 상태"
echo "  journalctl -u ai-news-bot -f           # 봇 로그 실시간"
echo "  journalctl -u ai-news-daily -n 50      # 마지막 뉴스 발송 로그"
echo ""
echo "🕘 다음 발송 시간 확인:"
echo "  systemctl list-timers ai-news-daily.timer"
echo ""
echo "⚡ 즉시 테스트 발송:"
echo "  systemctl start ai-news-daily.service"
echo ""
echo "🔄 코드 업데이트 (git pull 후 재시작):"
echo "  sudo bash $APP_DIR/deploy/update.sh"
