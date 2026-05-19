#!/bin/bash
# ==================================================
# AI News Bot — nohup 실행 스크립트
# 사용법: bash run.sh
#
# 시작:  bash run.sh
# 중지:  bash run.sh stop
# 상태:  bash run.sh status
# 로그:  bash run.sh logs
# ==================================================

APP_DIR="$(cd "$(dirname "$0")" && pwd)"
PYTHON="$(command -v python3 || command -v python)"
LOG_DIR="$APP_DIR/logs"
BOT_PID="$APP_DIR/bot.pid"
SCHEDULER_PID="$APP_DIR/scheduler.pid"

mkdir -p "$LOG_DIR"

stop() {
    echo "🛑 프로세스 중지 중..."
    for PID_FILE in "$BOT_PID" "$SCHEDULER_PID"; do
        if [ -f "$PID_FILE" ]; then
            PID=$(cat "$PID_FILE")
            if kill -0 "$PID" 2>/dev/null; then
                kill "$PID"
                echo "  종료: PID $PID"
            fi
            rm -f "$PID_FILE"
        fi
    done
    echo "✅ 중지 완료"
}

status() {
    echo "📊 프로세스 상태:"
    for NAME in bot scheduler; do
        PID_FILE="$APP_DIR/${NAME}.pid"
        if [ -f "$PID_FILE" ]; then
            PID=$(cat "$PID_FILE")
            if kill -0 "$PID" 2>/dev/null; then
                echo "  ✅ $NAME 실행 중 (PID: $PID)"
            else
                echo "  ❌ $NAME 종료됨 — PID 파일 정리 (로그: bash run.sh logs)"
                rm -f "$PID_FILE"
            fi
        else
            echo "  ⬜ $NAME 실행 안 됨"
        fi
    done
}

logs() {
    echo "=== 봇 로그 (최근 30줄) ==="
    tail -30 "$LOG_DIR/bot.log" 2>/dev/null || echo "(로그 없음)"
    echo ""
    echo "=== 스케줄러 로그 (최근 20줄) ==="
    tail -20 "$LOG_DIR/scheduler.log" 2>/dev/null || echo "(로그 없음)"
}

start() {
    # .env 확인
    if [ ! -f "$APP_DIR/.env" ]; then
        echo "❌ .env 파일이 없습니다. 먼저 생성하세요:"
        echo "   cp $APP_DIR/.env.example $APP_DIR/.env"
        echo "   nano $APP_DIR/.env"
        exit 1
    fi

    # 의존성 설치
    echo "📦 패키지 설치 중..."
    pip3 install --quiet -r "$APP_DIR/requirements.txt"
    echo "✅ 의존성 설치 완료"

    # 이미 실행 중인지 확인
    if [ -f "$BOT_PID" ] && kill -0 "$(cat "$BOT_PID")" 2>/dev/null; then
        echo "⚠️  봇이 이미 실행 중입니다. (PID: $(cat "$BOT_PID"))"
        echo "   먼저 중지하려면: bash run.sh stop"
        exit 1
    fi

    cd "$APP_DIR"

    # 1) 디스코드 봇 (항상 켜져 있음 — !ask 응답)
    nohup "$PYTHON" discord_bot.py >> "$LOG_DIR/bot.log" 2>&1 &
    echo $! > "$BOT_PID"
    echo "🤖 디스코드 봇 시작 (PID: $!)"

    # 2) 스케줄러 (매일 오전 9시 KST 뉴스 발송)
    nohup "$PYTHON" scheduler.py >> "$LOG_DIR/scheduler.log" 2>&1 &
    echo $! > "$SCHEDULER_PID"
    echo "⏰ 스케줄러 시작 (PID: $!)"

    echo ""
    echo "✅ 완료! 로그 확인: bash run.sh logs"
    echo "   실시간 봇 로그: tail -f $LOG_DIR/bot.log"
    echo "   실시간 스케줄러: tail -f $LOG_DIR/scheduler.log"
}

case "${1}" in
    ""| start) start ;;
    stop)    stop ;;
    status)  status ;;
    logs)    logs ;;
    restart)
        # PID 파일 기반 종료
        stop
        # PID 파일에 없는 잔여 프로세스도 전부 종료
        pkill -f scheduler.py 2>/dev/null && echo "  잔여 scheduler.py 종료" || true
        pkill -f discord_bot.py 2>/dev/null && echo "  잔여 discord_bot.py 종료" || true
        # PID 파일 잔여물 정리
        rm -f "$BOT_PID" "$SCHEDULER_PID"
        sleep 2
        start
        ;;
    *)
        echo "사용법: bash run.sh [start|stop|status|logs|restart]"
        exit 1
        ;;
esac
