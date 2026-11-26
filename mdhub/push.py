#!/usr/bin/env python3
"""MarkdownHub 文档推送 CLI：把本地 md/html 发布到远端 MarkdownHub 并自动索引。

用法:
  python3 push.py --file doc.md                          # 推到远端 doc.md（同名覆盖=更新）
  python3 push.py --file report.html --name pages/r.html # 指定远端相对路径
  python3 push.py --file doc.md --host http://max09.adsys.shrdt.qihoo.net:18123 --token TOK

host/token 配置优先级: 命令行参数 > 环境变量 MDHUB_HOST/MDHUB_TOKEN > ~/.mdhub-push.json
（配置文件示例: {"host": "...", "token": "..."}，建议 chmod 600）
"""
import argparse
import base64
import json
import os
import sys
import urllib.error
import urllib.request

CONFIG_FILE = os.path.expanduser("~/.mdhub-push.json")


def load_settings():
    """返回 (host, token)，按优先级合并。"""
    host, token = "", ""
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            cfg = json.load(f)
        host = cfg.get("host", "")
        token = cfg.get("token", "")
    except (OSError, ValueError):
        pass
    host = os.environ.get("MDHUB_HOST") or host
    token = os.environ.get("MDHUB_TOKEN") or token
    return host, token


def push(host, token, name, text):
    payload = json.dumps({"name": name, "text": text}).encode("utf-8")
    req = urllib.request.Request(
        host.rstrip("/") + "/api/publish",
        data=payload,
        headers={"Content-Type": "application/json", "X-Publish-Token": token},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return resp.status, json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", "replace")
        try:
            return e.code, json.loads(body)
        except ValueError:
            return e.code, {"error": body[:200]}
    except urllib.error.URLError as e:
        return 0, {"error": "连接失败: %s" % e.reason}


def main():
    ap = argparse.ArgumentParser(description="推送本地文档到 MarkdownHub")
    ap.add_argument("--file", required=True, help="本地 md/html 文件路径")
    ap.add_argument("--name", default=None, help="远端相对路径（默认取本地文件名）")
    ap.add_argument("--host", default=None)
    ap.add_argument("--token", default=None)
    args = ap.parse_args()

    cfg_host, cfg_token = load_settings()
    host = args.host or cfg_host
    token = args.token or cfg_token
    if not host or not token:
        print("缺少 host/token：用 --host/--token、环境变量 MDHUB_HOST/MDHUB_TOKEN 或配置 "
              + CONFIG_FILE, file=sys.stderr)
        sys.exit(1)

    path = os.path.abspath(args.file)
    if not os.path.isfile(path):
        print("本地文件不存在: %s" % path, file=sys.stderr)
        sys.exit(1)
    name = args.name or os.path.basename(path)
    if not name.lower().endswith((".md", ".html", ".htm")):
        print("仅支持 .md/.html 文件", file=sys.stderr)
        sys.exit(1)

    with open(path, "rb") as f:
        raw = f.read()
    # 编码兜底：utf-8 为主，gbk 兜底（与服务端 reader 一致）
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        text = raw.decode("gbk")

    status, data = push(host, token, name, text)
    if status == 201:
        print("已发布: %s/doc/%s/  （同名重复推送=更新）" % (host.rstrip("/"), data["entry"]["id"]))
    else:
        print("推送失败 [%s]: %s" % (status or "网络", data.get("error", "")), file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
