#!/usr/bin/env python
"""MarkdownHub 管理命令入口：set_password / token。"""
import argparse
import getpass
import sys

from mdhub import config


def main():
    parser = argparse.ArgumentParser(description="MarkdownHub admin commands")
    sub = parser.add_subparsers(dest="command", required=True)

    sp = sub.add_parser("set_password", help="设置管理员用户名与密码")
    sp.add_argument("--username", default="admin")
    sp.add_argument("--password", default=None, help="不传则交互式输入")

    sub.add_parser("token", help="显示推送令牌（无则生成），供本机 push CLI 配置")

    args = parser.parse_args()
    if args.command == "set_password":
        password = args.password or getpass.getpass("输入密码: ")
        if len(password) < 4:
            print("密码至少 4 位", file=sys.stderr)
            sys.exit(1)
        config.set_password(args.username, password)
        print(f"已设置管理员 {args.username} 的凭证（PBKDF2 哈希已写入 config.json）")
    elif args.command == "token":
        print(config.get_or_create_publish_token())


if __name__ == "__main__":
    main()
