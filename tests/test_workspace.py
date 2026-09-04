"""ticket 10：workspace 新建与删除语义。"""
import json
import os

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


def _login(client):
    client.post("/api/login", json={"username": "admin", "password": "s3cret!"})


@pytest.fixture()
def workspace(app, tmp_path, monkeypatch):
    ws = str(tmp_path / "workspace")
    os.makedirs(ws, exist_ok=True)
    app.config["WORKSPACE"] = ws
    return ws


def test_create_file_in_workspace(client, with_password, workspace):
    _login(client)
    r = client.post("/api/file", json={"name": "notes/new.md", "text": "# 新文件"})
    assert r.status_code == 201
    data = r.get_json()
    assert data["entry"]["type"] == "file"
    full = data["entry"]["path"]
    assert full.startswith(workspace)
    assert os.path.exists(full)  # 真实文件已创建
    with open(full, encoding="utf-8") as f:
        assert f.read() == "# 新文件"
    # 自动入索引，访客可见
    ids = [e["id"] for e in client.get("/api/list").get_json()["entries"]]
    assert data["entry"]["id"] in ids


def test_create_requires_workspace(client, with_password, workspace):
    _login(client)
    r = client.post("/api/file", json={"name": "../../etc/evil.md", "text": "x"})
    assert r.status_code == 400
    r = client.post("/api/file", json={"name": "/etc/evil.md", "text": "x"})
    assert r.status_code == 400


def test_create_rejects_existing(client, with_password, workspace):
    _login(client)
    r = client.post("/api/file", json={"name": "dup.md", "text": "a"})
    assert r.status_code == 201
    r = client.post("/api/file", json={"name": "dup.md", "text": "b"})
    assert r.status_code == 409


def test_create_requires_auth(client, with_password, workspace):
    assert client.post("/api/file", json={"name": "x.md", "text": "x"}).status_code == 401


def test_delete_workspace_file_removes_real_file(client, with_password, workspace):
    _login(client)
    r = client.post("/api/file", json={"name": "temp.md", "text": "t"})
    eid = r.get_json()["entry"]["id"]
    path = r.get_json()["entry"]["path"]
    r = client.delete(f"/api/file/{eid}")
    assert r.status_code == 200
    assert not os.path.exists(path)  # 真实文件被删除
    ids = [e["id"] for e in client.get("/api/list").get_json()["entries"]]
    assert eid not in ids  # 索引同时移除


def test_delete_external_entry_keeps_file(client, with_password, workspace, tmp_path):
    _login(client)
    p = tmp_path / "external.md"
    p.write_text("ext", encoding="utf-8")
    eid = client.post("/api/entry", json={"path": str(p)}).get_json()["entry"]["id"]
    # /api/file/<id> 对外部条目必须拒绝（语义不同）
    r = client.delete(f"/api/file/{eid}")
    assert r.status_code == 409
    assert os.path.exists(str(p))
    # /api/entry/<id> 仍然可用（仅取消共享）
    assert client.delete(f"/api/entry/{eid}").status_code == 200
    assert os.path.exists(str(p))


def test_delete_file_requires_auth(client, with_password, workspace):
    _login(client)
    r = client.post("/api/file", json={"name": "t2.md", "text": "t"})
    eid = r.get_json()["entry"]["id"]
    client.post("/api/logout")
    assert client.delete(f"/api/file/{eid}").status_code == 401
