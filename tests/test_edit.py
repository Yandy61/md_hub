"""ticket 09：在线编辑写回 + .backups 备份。"""
import json
import os
import time

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
def indexed(client, with_password, tmp_path):
    _login(client)  # 先登录再建索引
    p = tmp_path / "edit.md"
    p.write_text("# v1\n", encoding="utf-8")
    r = client.post("/api/entry", json={"path": str(p)})
    return r.get_json()["entry"]


def test_get_raw_for_edit(client, indexed):
    r = client.get(f"/api/raw/{indexed['id']}/")
    assert r.status_code == 200
    assert r.get_json()["text"] == "# v1\n"


def test_put_writes_back_to_source(client, indexed, tmp_path):
    r = client.put(f"/api/doc/{indexed['id']}/", json={"text": "# v2\n"})
    assert r.status_code == 200
    with open(indexed["path"], encoding="utf-8") as f:
        assert f.read() == "# v2\n"
    # 访客 API 读到新内容
    assert client.get(f"/api/doc/{indexed['id']}/").get_json()["text"] == "# v2\n"


def test_put_creates_backup(client, indexed, app):
    client.put(f"/api/doc/{indexed['id']}/", json={"text": "# v2\n"})
    backups = os.listdir(app.config["BACKUP_DIR"])
    assert len(backups) == 1
    with open(os.path.join(app.config["BACKUP_DIR"], backups[0]), encoding="utf-8") as f:
        assert f.read() == "# v1\n"  # 备份的是写回前的内容


def test_put_requires_auth(client, with_password, indexed):
    # 登出后的 client 写回被拒且原文件未动（indexed fixture 已登录，先登出）
    client.post("/api/logout")
    r = client.put(f"/api/doc/{indexed['id']}/", json={"text": "hacked"})
    assert r.status_code == 401
    with open(indexed["path"], encoding="utf-8") as f:
        assert f.read() == "# v1\n"


def test_put_missing_text_400(client, with_password, indexed):
    _login(client)
    assert client.put(f"/api/doc/{indexed['id']}/", json={}).status_code == 400


def test_backup_rotation_keeps_n(client, indexed, app, monkeypatch):
    app.config["BACKUP_KEEP"] = 3
    for i in range(5):
        client.put(f"/api/doc/{indexed['id']}/", json={"text": f"# v{i+2}\n"})
        time.sleep(0.01)  # 保证时间戳不同
    backups = os.listdir(app.config["BACKUP_DIR"])
    assert len(backups) == 3  # 只保留最近 3 份
