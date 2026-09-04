#!/bin/bash
# MarkdownHub 停止脚本：按 pid 文件停止并清理
set -e
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PID_FILE="$PROJECT_DIR/data/mdhub.pid"

if [ ! -f "$PID_FILE" ]; then
  echo "未找到 pid 文件，MarkdownHub 可能未在运行"
  exit 0
fi

PID="$(cat "$PID_FILE")"
if kill -0 "$PID" 2>/dev/null; then
  kill "$PID"
  for _ in $(seq 1 10); do
    kill -0 "$PID" 2>/dev/null || break
    sleep 0.5
  done
  kill -0 "$PID" 2>/dev/null && kill -9 "$PID" || true
  echo "MarkdownHub 已停止 (pid $PID)"
else
  echo "进程 $PID 已不存在"
fi
rm -f "$PID_FILE"
