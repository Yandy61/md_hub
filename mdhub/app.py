"""MarkdownHub — 内网 markdown 分享服务（Flask 应用工厂）。"""
import os

from flask import Flask, jsonify

from mdhub import config


def create_app():
    app = Flask(__name__, static_folder="static", static_url_path="/static")
    app.secret_key = config.load_config()["secret_key"]

    @app.get("/api/health")
    def health():
        return jsonify({"status": "ok"})

    return app


def main():
    import argparse

    parser = argparse.ArgumentParser(description="MarkdownHub")
    parser.add_argument("--port", type=int, default=None)
    args = parser.parse_args()
    cfg = config.load_config()
    os.makedirs(config.DATA_DIR, exist_ok=True)
    app = create_app()
    app.run(
        host=cfg["host"],
        port=args.port or cfg["port"],
        debug=False,
        use_reloader=False,
    )


if __name__ == "__main__":
    main()
