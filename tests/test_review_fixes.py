"""code-review 修复回归：符号链接越界、坏链接健壮性、并发、编码、删除语义、备份碰撞、死配置。"""
import json
import os
import threading

import pytest

from mdhub import config as cfgmod


@pytest.fixture()
def with_password(app, tmp_path):
    data_dir = os.environ["MDHUB_DATA_DIR"]
    os.makedirs(data_dir, exist_ok=True)
    cfg_path = os.path.join(data_dir, "config.json")
    cfg = {"username": "admin", "password_hash": cfgmod.hash_password("s3cret!")}
    with open(cfg_path, "w", encoding="utf-8") as f:
        json.dump(cfg, f)
    app.config["username"] = "admin"
    return app


def _add(app, path, type_):
    from mdhub.registry import Registry

    return Registry(app.config["REGISTRY_PATH"]).add(path, type_)


def _login(client):
    client.post("/api/login", json={"username": "admin", "password": "s3cret!"})


# --- #2 符号链接越界 ---

def test_symlink_escape_asset_blocked(client, app, tmp_path):
    d = tmp_path / "shared"
    d.mkdir()
    (d / "a.md").write_text("a", encoding="utf-8")
    os.symlink("/etc/passwd", str(d / "leak"))  # 指向共享树外
    entry = _add(app, d, "dir")
    assert client.get(f"/api/asset/{entry['id']}/leak").status_code == 404


def test_symlink_escape_doc_put_blocked(client, app, with_password, tmp_path):
    d = tmp_path / "shared2"
    d.mkdir()
    (d / "a.md").write_text("a", encoding="utf-8")
    os.symlink("/tmp/evil_target.md", str(d / "esc.md"))
    entry = _add(app, d, "dir")
    _login(client)
    # 写入穿透符号链接的目标 → 拒绝
    assert client.put(f"/api/doc/{entry['id']}/esc.md", json={"text": "pwn"}).status_code == 404
    assert not os.path.exists("/tmp/evil_target.md")


def test_symlink_within_tree_still_served(client, app, tmp_path):
    d = tmp_path / "shared3"
    (d / "sub").mkdir(parents=True)
    (d / "a.md").write_text("a", encoding="utf-8")
    (d / "sub" / "real.png").write_bytes(b"PNG")
    os.symlink(str(d / "sub" / "real.png"), str(d / "link.png"))  # 树内软链合法
    entry = _add(app, d, "dir")
    assert client.get(f"/api/asset/{entry['id']}/link.png").data == b"PNG"


# --- #4 坏符号链接不让 /api/list 500 ---

def test_broken_symlink_does_not_break_list(client, app, tmp_path):
    d = tmp_path / "withbroken"
    d.mkdir()
    (d / "ok.md").write_text("ok", encoding="utf-8")
    os.symlink(str(tmp_path / "nonexistent.md"), str(d / "broken.md"))
    entry = _add(app, d, "dir")
    r = client.get("/api/list")
    assert r.status_code == 200
    rels = [f["rel"] for f in r.get_json()["entries"][0]["files"]]
    assert "ok.md" in rels
    broken = next(f for f in r.get_json()["entries"][0]["files"] if f["rel"] == "broken.md")
    assert broken.get("missing") is True


# --- #5 registry 并发安全 ---

def test_registry_concurrent_add_no_loss(app, tmp_path):
    from mdhub.registry import Registry

    reg = Registry(app.config["REGISTRY_PATH"])
    paths = []
    for i in range(20):
        p = tmp_path / f"conc_{i}.md"
        p.write_text("x", encoding="utf-8")
        paths.append(str(p))

    ids = []
    lock = threading.Lock()

    def worker(path):
        e = reg.add(path, "file")
        with lock:
            ids.append(e["id"])

    threads = [threading.Thread(target=worker, args=(p,)) for p in paths]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert len(ids) == 20
    assert len(set(ids)) == 20  # id 无重复
    assert len(reg.entries()) == 20  # 条目无丢失


# --- #6 GBK 文件写回保持原编码 ---

def test_put_preserves_gbk_encoding(client, app, with_password, tmp_path):
    p = tmp_path / "legacy_gbk.md"
    p.write_bytes("中文编码保留测试".encode("gbk"))
    entry = _add(app, str(p), "file")
    _login(client)
    r = client.put(f"/api/doc/{entry['id']}/", json={"text": "更新后的中文内容"})
    assert r.status_code == 200
    raw = open(str(p), "rb").read()
    assert raw.decode("gbk") == "更新后的中文内容"  # 仍是 GBK


def test_put_new_chars_fall_back_utf8(client, app, with_password, tmp_path):
    p = tmp_path / "legacy2.md"
    p.write_bytes("中文".encode("gbk"))
    entry = _add(app, str(p), "file")
    _login(client)
    client.put(f"/api/doc/{entry['id']}/", json={"text": "中文 with émoji 🎉"})
    raw = open(str(p), "rb").read()
    assert "🎉" in raw.decode("utf-8")  # GBK 表不下的字符回退 UTF-8


# --- #7 删除语义按来源而非位置 ---

def test_external_file_in_workspace_not_really_deleted(client, app, with_password, tmp_path):
    ws = str(tmp_path / "ws")
    os.makedirs(ws)
    app.config["WORKSPACE"] = ws
    preexisting = tmp_path / "ws" / "put_here_by_human.md"
    preexisting.write_text("precious", encoding="utf-8")
    entry = _add(app, str(preexisting), "file")  # 外部文件，只是恰好位于 workspace
    _login(client)
    r = client.delete(f"/api/file/{entry['id']}")
    assert r.status_code == 409  # 拒绝真删
    assert preexisting.exists()
    # 仅取消共享仍可用
    assert client.delete(f"/api/entry/{entry['id']}").status_code == 200
    assert preexisting.exists()


def test_created_in_service_flag_survives(client, app, with_password, tmp_path):
    ws = str(tmp_path / "ws2")
    os.makedirs(ws)
    app.config["WORKSPACE"] = ws
    _login(client)
    r = client.post("/api/file", json={"name": "made.md", "text": "x"})
    e = r.get_json()["entry"]
    from mdhub.registry import Registry

    stored = {x["id"]: x for x in Registry(app.config["REGISTRY_PATH"]).entries()}
    assert stored[e["id"]]["created_in_service"] is True


# --- #9 备份 digest 碰撞 ---

def test_backup_digest_no_collision(app, tmp_path):
    from mdhub.backup import backup_file

    a = tmp_path / "my docs"
    b = tmp_path / "my_docs"
    a.mkdir()
    b.mkdir()
    (a / "f.md").write_text("A", encoding="utf-8")
    (b / "f.md").write_text("B", encoding="utf-8")
    backup_file(str(a / "f.md"), str(tmp_path / "bk"), keep=10)
    backup_file(str(b / "f.md"), str(tmp_path / "bk"), keep=10)
    backup_file(str(a / "f.md"), str(tmp_path / "bk"), keep=10)
    files = os.listdir(str(tmp_path / "bk"))
    # A 的第二次备份不应删掉 B 的备份
    assert len(files) == 3


# --- #10 死配置生效 ---

def test_config_workspace_and_backup_keep_applied(app, tmp_path, monkeypatch):
    data_dir = os.environ["MDHUB_DATA_DIR"]
    os.makedirs(data_dir, exist_ok=True)
    cfg_path = os.path.join(data_dir, "config.json")
    ws = str(tmp_path / "custom_ws")
    os.makedirs(ws)
    with open(cfg_path, "w", encoding="utf-8") as f:
        json.dump({"workspace": ws, "backup_keep": 3}, f)
    # 重建 app（模拟重启加载配置）
    import importlib
    import sys

    for mod in [m for m in list(sys.modules) if m == "mdhub" or m.startswith("mdhub.")]:
        del sys.modules[mod]
    import mdhub.app as app_module

    app2 = app_module.create_app()
    assert app2.config["WORKSPACE"] == ws
    assert app2.config["BACKUP_KEEP"] == 3
