"""ticket 08：索引管理（增/删/源丢失）。"""
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


def _entry(client, eid):
    entries = client.get("/api/list").get_json()["entries"]
    return next(x for x in entries if x["id"] == eid)


def test_add_file_entry(client, with_password, tmp_path):
    _login(client)
    p = tmp_path / "doc.md"
    p.write_text("# t", encoding="utf-8")
    r = client.post("/api/entry", json={"path": str(p)})
    assert r.status_code == 201
    assert r.get_json()["entry"]["type"] == "file"
    ids = [e["id"] for e in client.get("/api/list").get_json()["entries"]]
    assert r.get_json()["entry"]["id"] in ids  # 访客立即可见


def test_add_entry_expands_tilde(client, with_password, tmp_path, monkeypatch):
    # ~/ 应展开为 HOME（启动服务用户的 home）
    _login(client)
    home = tmp_path / "homedir"
    home.mkdir()
    (home / "note.md").write_text("n", encoding="utf-8")
    monkeypatch.setenv("HOME", str(home))
    r = client.post("/api/entry", json={"path": "~/note.md"})
    assert r.status_code == 201
    assert r.get_json()["entry"]["path"] == str(home / "note.md")


def test_add_dir_entry(client, with_password, tmp_path):
    _login(client)
    d = tmp_path / "docs"
    d.mkdir()
    (d / "a.md").write_text("a", encoding="utf-8")
    r = client.post("/api/entry", json={"path": str(d)})
    assert r.status_code == 201
    assert r.get_json()["entry"]["type"] == "dir"


def test_add_duplicate_path_idempotent(client, with_password, tmp_path):
    _login(client)
    p = tmp_path / "dup.md"
    p.write_text("d", encoding="utf-8")
    r1 = client.post("/api/entry", json={"path": str(p)})
    r2 = client.post("/api/entry", json={"path": str(p)})
    assert r1.get_json()["entry"]["id"] == r2.get_json()["entry"]["id"]
    assert len(client.get("/api/list").get_json()["entries"]) == 1


def test_add_missing_path_404(client, with_password):
    _login(client)
    assert client.post("/api/entry", json={"path": "/nonexistent/xyz.md"}).status_code == 404


def test_add_empty_path_400(client, with_password):
    _login(client)
    assert client.post("/api/entry", json={}).status_code == 400


def test_add_requires_auth(client, with_password, tmp_path):
    p = tmp_path / "x.md"
    p.write_text("x", encoding="utf-8")
    assert client.post("/api/entry", json={"path": str(p)}).status_code == 401


def test_remove_entry_keeps_source_file(client, with_password, tmp_path):
    _login(client)
    p = tmp_path / "keep.md"
    p.write_text("keep me", encoding="utf-8")
    entry = client.post("/api/entry", json={"path": str(p)}).get_json()["entry"]
    r = client.delete(f"/api/entry/{entry['id']}")
    assert r.status_code == 200
    assert os.path.exists(str(p))  # 原文件完好
    assert not any(e["id"] == entry["id"] for e in client.get("/api/list").get_json()["entries"])


def test_remove_requires_auth(client, with_password):
    assert client.delete("/api/entry/1").status_code == 401


def test_remove_unknown_404(client, with_password):
    _login(client)
    assert client.delete("/api/entry/999").status_code == 404
