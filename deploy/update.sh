#!/bin/bash
# ==================================================
# AI News Bot — 코드 업데이트 스크립트
# 사용법: sudo bash /opt/ai-news-bot/deploy/update.sh
# ==================================================
set -e

APP_DIR="/opt/ai-news-bot"

echo "🔄 코드 업데이트 중..."
git -C "$APP_DIR" pull

echo "📦 의존성 업데이트 중..."
pip3 install --quiet -r "$APP_DIR/requirements.txt"

echo "🔁 봇 재시작 중..."
systemctl restart ai-news-bot

echo "✅ 업데이트 완료!"
systemctl status ai-news-bot --no-pager
