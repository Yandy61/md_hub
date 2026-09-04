"""MarkdownHub — 内网 markdown 分享服务（Flask 应用工厂）。"""
import functools
import os

from flask import Flask, jsonify, request, send_file, send_from_directory, session

from mdhub import config
from mdhub.reader import read_text
from mdhub.registry import Registry
from mdhub.scanner import scan_dir


def create_app():
    app = Flask(__name__, static_folder="static", static_url_path="/static")
    app = Flask(__name__, static_folder="static", static_url_path="/static")
    app.config.update(
        REGISTRY_PATH=config.REGISTRY_PATH,
        WORKSPACE=config.WORKSPACE_DIR,
        BACKUP_DIR=config.BACKUP_DIR,
        BACKUP_KEEP=10,
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Strict",
    )
    app.secret_key = config.load_config()["secret_key"]
    registry = Registry(config.REGISTRY_PATH)

    def is_admin():
        return bool(session.get("admin"))

    def admin_required(fn):
        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            if not is_admin():
                return jsonify({"error": "authentication required"}), 401
            return fn(*args, **kwargs)
        return wrapper

    @app.get("/api/me")
    def me():
        return jsonify({"authenticated": is_admin()})

    @app.post("/api/login")
    def login():
        body = request.get_json(silent=True) or {}
        username = body.get("username")
        password = body.get("password")
        if not username or not password:
            return jsonify({"error": "username and password required"}), 400
        cfg = config.load_config()
        stored = cfg.get("password_hash")
        if not stored or username != cfg.get("username") or not config.verify_password(password, stored):
            return jsonify({"error": "invalid credentials"}), 401
        session.clear()
        session["admin"] = True
        return jsonify({"authenticated": True})

    @app.post("/api/logout")
    def logout():
        session.clear()
        return jsonify({"authenticated": False})

    @app.post("/api/entry")
    @admin_required
    def add_entry():
        body = request.get_json(silent=True) or {}
        path = body.get("path")
        if not path:
            return jsonify({"error": "path required"}), 400
        if not os.path.exists(path):
            return jsonify({"error": "path not found"}), 404
        type_ = "dir" if os.path.isdir(path) else "file"
        entry = registry.add(path, type_)
        return jsonify({"entry": entry}), 201

    @app.get("/api/health")
    def health():
        return jsonify({"status": "ok"})

    @app.get("/")
    def index_page():
        return send_from_directory(app.template_folder, "list.html")

    @app.get("/doc/<entry_id>/")
    @app.get("/doc/<entry_id>")
    def doc_page(entry_id):
        return send_from_directory(app.template_folder, "doc.html")

    @app.get("/api/list")
    def list_entries():
        out = []
        for e in registry.entries():
            item = {"id": e["id"], "path": e["path"], "type": e["type"]}
            if e["type"] == "file":
                item["missing"] = not os.path.exists(e["path"])
                if not item["missing"]:
                    st = os.stat(e["path"])
                    item["mtime"] = int(st.st_mtime)
                    item["size"] = st.st_size
            else:  # dir：递归扫描
                if os.path.isdir(e["path"]):
                    item["missing"] = False
                    files = []
                    for rel in scan_dir(e["path"]):
                        fp = os.path.join(e["path"], rel.replace("/", os.sep))
                        fst = os.stat(fp)
                        files.append({"rel": rel, "mtime": int(fst.st_mtime), "size": fst.st_size})
                    item["files"] = files
                else:
                    item["missing"] = True
                    item["files"] = []
            out.append(item)
        return jsonify({"entries": out})

    def _resolve(entry_id, subpath):
        """定位条目内文件。返回 (abs_path, None) 或 (None, error_response)。"""
        entries = {e["id"]: e for e in registry.entries()}
        entry = entries.get(entry_id)
        if not entry:
            return None, (jsonify({"error": "no such entry"}), 404)
        base = entry["path"]
        if entry["type"] == "file":
            if subpath:
                return None, (jsonify({"error": "not found"}), 404)
            return base, None
        # dir 条目：解析子路径并拒绝越界
        target = os.path.normpath(os.path.join(base, subpath))
        if not (target == base or target.startswith(base + os.sep)):
            return None, (jsonify({"error": "traversal blocked"}), 404)
        return target, None

    def _serve_file(path, entry_id):
        if not os.path.isfile(path):
            return jsonify({"error": "not found"}), 404
        try:
            text, enc = read_text(path)
        except (UnicodeDecodeError, OSError):
            return jsonify({"error": "unreadable"}), 415
        st = os.stat(path)
        return jsonify({
            "id": entry_id,
            "path": path,
            "text": text,
            "encoding": enc,
            "mtime": int(st.st_mtime),
            "size": st.st_size,
        })

    def _resolve_asset(entry_id, subpath):
        """资产解析：dir 条目以目录为界，file 条目以其所在目录为界。"""
        entries = {e["id"]: e for e in registry.entries()}
        entry = entries.get(entry_id)
        if not entry:
            return None, (jsonify({"error": "no such entry"}), 404)
        base = entry["path"]
        if entry["type"] == "file":
            base = os.path.dirname(base)
        target = os.path.normpath(os.path.join(base, subpath))
        if not (target == base or target.startswith(base + os.sep)):
            return None, (jsonify({"error": "traversal blocked"}), 404)
        return target, None

    @app.get("/api/asset/<entry_id>/<path:subpath>")
    def get_asset(entry_id, subpath):
        path, err = _resolve_asset(entry_id, subpath)
        if err is not None:
            return err
        if not os.path.isfile(path):
            return jsonify({"error": "not found"}), 404
        return send_file(path)

    @app.get("/api/doc/<entry_id>/")
    def get_doc(entry_id):
        path, err = _resolve(entry_id, "")
        if err is not None:
            return err
        return _serve_file(path, entry_id)

    @app.get("/api/doc/<entry_id>/<path:subpath>")
    def get_doc_sub(entry_id, subpath):
        path, err = _resolve(entry_id, subpath)
        if err is not None:
            return err
        return _serve_file(path, entry_id)

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
