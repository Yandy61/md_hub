"""文档推送接口 /api/publish：token 鉴权、publish_dir 边界、幂等更新。"""
import json
import os

import pytest

from mdhub import config as cfgmod

TOKEN = "testtoken123"


@pytest.fixture()
def with_token(app, tmp_path):
    """写入凭证与推送令牌；发布目录指向临时路径。"""
    data_dir = os.environ["MDHUB_DATA_DIR"]
    os.makedirs(data_dir, exist_ok=True)
    cfg = {
        "username": "admin",
        "password_hash": cfgmod.hash_password("s3cret!"),
        "publish_token": TOKEN,
        "publish_dir": str(tmp_path / "published"),
    }
    with open(os.path.join(data_dir, "config.json"), "w", encoding="utf-8") as f:
        json.dump(cfg, f)
    return app


def test_publish_requires_token(client, with_token):
    r = client.post("/api/publish", json={"name": "a.md", "text": "hi"})
    assert r.status_code == 401
    r = client.post("/api/publish", json={"name": "a.md", "text": "hi"},
                    headers={"X-Publish-Token": "wrong"})
    assert r.status_code == 401


def test_publish_creates_and_indexes(client, with_token, app):
    hdr = {"X-Publish-Token": TOKEN}
    r = client.post("/api/publish", json={"name": "notes/a.md", "text": "# 推送文档"},
                    headers=hdr)
    assert r.status_code == 201
    entry = r.get_json()["entry"]
    assert entry["type"] == "file" and entry["created_in_service"] is True
    # 真实文件落在 published/notes/a.md
    from mdhub.registry import Registry

    stored = {e["id"]: e for e in Registry(app.config["REGISTRY_PATH"]).entries()}
    assert stored[entry["id"]]["path"].endswith(os.path.join("published", "notes", "a.md"))
    # 访客可读
    assert "推送文档" in client.get(f"/api/doc/{entry['id']}/").get_json()["text"]


def test_publish_same_name_updates_in_place(client, with_token):
    hdr = {"X-Publish-Token": TOKEN}
    r1 = client.post("/api/publish", json={"name": "doc.md", "text": "v1"}, headers=hdr)
    r2 = client.post("/api/publish", json={"name": "doc.md", "text": "v2"}, headers=hdr)
    assert r1.status_code == r2.status_code == 201
    assert r1.get_json()["entry"]["id"] == r2.get_json()["entry"]["id"]  # 同条目
    assert client.get(f"/api/doc/{r2.get_json()['entry']['id']}/").get_json()["text"] == "v2"


def test_publish_rejects_bad_name(client, with_token):
    hdr = {"X-Publish-Token": TOKEN}
    assert client.post("/api/publish", json={"name": "../evil.md", "text": "x"},
                       headers=hdr).status_code == 400
    assert client.post("/api/publish", json={"name": "a.txt", "text": "x"},
                       headers=hdr).status_code == 400
    assert client.post("/api/publish", json={"name": "b.md"},
                       headers=hdr).status_code == 400


def test_publish_token_roundtrip(app, tmp_path, monkeypatch):
    """CLI token 命令：无则生成，再取不变。"""
    import subprocess
    import sys

    monkeypatch.setenv("MDHUB_DATA_DIR", str(tmp_path / "data"))
    for mod in [m for m in list(__import__("sys").modules) if m == "mdhub" or m.startswith("mdhub.")]:
        del __import__("sys").modules[mod]
    from mdhub import config as cfg2

    t1 = cfg2.get_or_create_publish_token()
    t2 = cfg2.get_or_create_publish_token()
    assert t1 == t2 and len(t1) >= 32
