#!/bin/bash
# MarkdownHub 启动脚本：nohup 后台运行，日志写 logs/，pid 写 data/mdhub.pid
set -e
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_DIR"

# conda base 环境（若存在）
if [ -f "$HOME/miniconda3/etc/profile.d/conda.sh" ]; then
  source "$HOME/miniconda3/etc/profile.d/conda.sh"
  conda activate base
fi

PORT="${MDHUB_PORT:-18123}"
LOG_DIR="$PROJECT_DIR/logs"
PID_FILE="$PROJECT_DIR/data/mdhub.pid"
mkdir -p "$LOG_DIR" "$PROJECT_DIR/data"

if [ -f "$PID_FILE" ] && kill -0 "$(cat "$PID_FILE")" 2>/dev/null; then
  echo "MarkdownHub 已在运行 (pid $(cat "$PID_FILE"))"
  exit 0
fi

LOG_FILE="$LOG_DIR/mdhub_$(date +%Y%m%d_%H%M%S).log"
nohup python -m mdhub.app --port "$PORT" >> "$LOG_FILE" 2>&1 &
echo $! > "$PID_FILE"
sleep 1
echo "MarkdownHub 已启动 (pid $(cat "$PID_FILE"), 端口 $PORT, 日志 $LOG_FILE)"
