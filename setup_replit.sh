#!/bin/bash
# Replit 초기 설정 스크립트
# Replit Shell에서 실행: bash setup_replit.sh

echo "=== Replit 환경변수 설정 ==="
echo ""

read -p "DISCORD_BOT_TOKEN: " token
read -p "GEMINI_API_KEY: " apikey

cat > .env << EOF
DISCORD_BOT_TOKEN=$token
GEMINI_API_KEY=$apikey
EOF

echo ""
echo "✅ .env 생성 완료!"
echo "▶ Run 버튼을 눌러 봇을 시작하세요."
