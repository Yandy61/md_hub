"""MarkdownHub — 内网 markdown 分享服务（Flask 应用工厂）。"""
import functools
import os

from flask import Flask, jsonify, request, send_file, send_from_directory, session

from mdhub import config
from mdhub.reader import read_text
from mdhub.registry import Registry
from mdhub.scanner import is_excluded, scan_dir


def _within(real_target, base):
    """realpath 边界检查：解析符号链接后比对（防软链越界）。"""
    rt = os.path.realpath(real_target)
    rb = os.path.realpath(base)
    return rt == rb or rt.startswith(rb + os.sep)


def create_app():
    app = Flask(__name__, static_folder="static", static_url_path="/static")
    cfg = config.load_config()
    app.config.update(
        REGISTRY_PATH=config.REGISTRY_PATH,
        WORKSPACE=cfg.get("workspace") or config.WORKSPACE_DIR,
        BACKUP_DIR=config.BACKUP_DIR,
        BACKUP_KEEP=cfg.get("backup_keep", 10),
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Strict",
        BROWSE_ROOT=os.path.expanduser("~"),
    )
    app.secret_key = cfg["secret_key"]
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

    @app.delete("/api/entry/<entry_id>")
    @admin_required
    def remove_entry(entry_id):
        if not registry.remove(entry_id):
            return jsonify({"error": "no such entry"}), 404
        return jsonify({"removed": entry_id})

    def _workspace_path(name):
        """把相对名解析到 workspace 内的绝对路径；越界返回 None。"""
        ws = os.path.abspath(app.config["WORKSPACE"])
        target = os.path.abspath(os.path.join(ws, name))
        if target != ws and not target.startswith(ws + os.sep):
            return None
        return target

    @app.post("/api/file")
    @admin_required
    def create_file():
        body = request.get_json(silent=True) or {}
        name = (body.get("name") or "").strip()
        text = body.get("text", "")
        if not name:
            return jsonify({"error": "name required"}), 400
        if not name.endswith(".md"):
            return jsonify({"error": "only .md files"}), 400
        path = _workspace_path(name)
        if path is None:
            return jsonify({"error": "path outside workspace"}), 400
        if os.path.exists(path):
            return jsonify({"error": "file exists"}), 409
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(text)
        entry = registry.add(path, "file", created_in_service=True)
        return jsonify({"entry": entry}), 201

    @app.delete("/api/file/<entry_id>")
    @admin_required
    def delete_file(entry_id):
        """删除服务新建的文件：索引移除 + 真实文件删除。

        语义按来源（created_in_service）而非当前位置判定：
        外部文件即使恰好位于 workspace 内也只允许取消共享。
        """
        entries = {e["id"]: e for e in registry.entries()}
        entry = entries.get(entry_id)
        if not entry:
            return jsonify({"error": "no such entry"}), 404
        if not entry.get("created_in_service"):
            return jsonify({"error": "not created by service — use unshare instead"}), 409
        if os.path.exists(entry["path"]):
            os.remove(entry["path"])
        registry.remove(entry_id)
        return jsonify({"deleted": entry_id})

    @app.get("/api/browse")
    @admin_required
    def browse():
        """目录浏览器：以 home 为根，允许经 home 下软链进入（realpath 后仍在许可根内）。"""
        root = app.config["BROWSE_ROOT"]
        # 许可根：home 的 realpath + home 下所有软链的 realpath 目标
        allowed_roots = {os.path.realpath(root)}
        try:
            for name in os.listdir(root):
                full = os.path.join(root, name)
                if os.path.islink(full):
                    allowed_roots.add(os.path.realpath(full))
        except OSError:
            pass

        def resolve(p):
            rp = os.path.realpath(p)
            for r in allowed_roots:
                if rp == r or rp.startswith(r + os.sep):
                    return rp
            return None

        path = request.args.get("path") or root
        current = resolve(path)
        if current is None or not os.path.isdir(current):
            return jsonify({"error": "path not allowed"}), 403

        dirs, files = [], []
        for name in os.listdir(current):
            if is_excluded(name):
                continue
            full = os.path.join(current, name)
            if os.path.isdir(full):
                dirs.append({"name": name, "path": os.path.realpath(full)})
            elif os.path.isfile(full) and name.endswith(".md"):
                files.append({"name": name, "path": os.path.realpath(full)})
        dirs.sort(key=lambda d: d["name"].lower())
        files.sort(key=lambda f: f["name"].lower())

        parent = resolve(os.path.dirname(current))
        return jsonify({
            "root": os.path.realpath(root),
            "current": current,
            "parent": parent,
            "dirs": dirs,
            "files": files,
        })

    @app.get("/api/health")
    def health():
        return jsonify({"status": "ok"})

    @app.get("/")
    def index_page():
        # 主界面需登录；文档预览页（/doc/*）保持匿名
        if is_admin():
            return send_from_directory(app.template_folder, "list.html")
        return send_from_directory(app.template_folder, "login.html")

    @app.get("/doc/<entry_id>/")
    @app.get("/doc/<entry_id>")
    @app.get("/doc/<entry_id>/<path:subpath>")
    def doc_page(entry_id, subpath=""):
        return send_from_directory(app.template_folder, "doc.html")

    @app.get("/api/list")
    @admin_required
    def list_entries():
        out = []
        for e in registry.entries():
            item = {"id": e["id"], "path": e["path"], "type": e["type"],
                    "created_in_service": bool(e.get("created_in_service"))}
            if e["type"] == "file":
                item["missing"] = not os.path.exists(e["path"])
                if not item["missing"]:
                    try:
                        st = os.stat(e["path"])
                    except OSError:
                        item["missing"] = True
                    else:
                        item["mtime"] = int(st.st_mtime)
                        item["size"] = st.st_size
            else:  # dir：递归扫描
                if os.path.isdir(e["path"]):
                    item["missing"] = False
                    files = []
                    for rel in scan_dir(e["path"]):
                        fp = os.path.join(e["path"], rel.replace("/", os.sep))
                        try:
                            fst = os.stat(fp)  # 坏符号链接/TOCTOU 不至于打挂列表
                        except OSError:
                            files.append({"rel": rel, "missing": True})
                            continue
                        files.append({"rel": rel, "mtime": int(fst.st_mtime), "size": fst.st_size})
                    item["files"] = files
                else:
                    item["missing"] = True
                    item["files"] = []
            out.append(item)
        return jsonify({"entries": out})

    def _resolve(entry_id, subpath):
        """定位条目内文件（realpath 边界检查）。返回 (abs_path, None) 或 (None, error_response)。"""
        entries = {e["id"]: e for e in registry.entries()}
        entry = entries.get(entry_id)
        if not entry:
            return None, (jsonify({"error": "no such entry"}), 404)
        base = entry["path"]
        if entry["type"] == "file":
            if subpath:
                return None, (jsonify({"error": "not found"}), 404)
            return base, None
        # dir 条目：解析子路径并拒绝越界（realpath 解析符号链接后比对）
        target = os.path.normpath(os.path.join(base, subpath))
        if not _within(target, base):
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
        """资产解析：dir 条目以目录为界，file 条目以其所在目录为界（realpath 边界）。"""
        entries = {e["id"]: e for e in registry.entries()}
        entry = entries.get(entry_id)
        if not entry:
            return None, (jsonify({"error": "no such entry"}), 404)
        base = entry["path"]
        if entry["type"] == "file":
            base = os.path.dirname(base)
        target = os.path.normpath(os.path.join(base, subpath))
        if not _within(target, base):
            return None, (jsonify({"error": "traversal blocked"}), 404)
        return target, None

    @app.get("/api/raw/<entry_id>/")
    @app.get("/api/raw/<entry_id>/<path:subpath>")
    @admin_required
    def get_raw(entry_id, subpath=""):
        """编辑器取原文（与访客 doc 相同内容，走鉴权）。"""
        path, err = _resolve(entry_id, subpath)
        if err is not None:
            return err
        return _serve_file(path, entry_id)

    @app.put("/api/doc/<entry_id>/")
    @app.put("/api/doc/<entry_id>/<path:subpath>")
    @admin_required
    def put_doc(entry_id, subpath=""):
        body = request.get_json(silent=True) or {}
        text = body.get("text")
        if text is None:
            return jsonify({"error": "text required"}), 400
        path, err = _resolve(entry_id, subpath)
        if err is not None:
            return err
        if not os.path.isfile(path):
            return jsonify({"error": "not found"}), 404
        try:
            from mdhub.backup import backup_file

            backup_file(path, app.config["BACKUP_DIR"], app.config["BACKUP_KEEP"])
        except OSError:
            pass  # 备份失败不阻塞写回
        from mdhub.reader import write_text

        write_text(path, text)  # 保留原编码（GBK 文件不被静默转码）
        return _serve_file(path, entry_id)

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
