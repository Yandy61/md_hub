"""ticket 07：管理员认证。"""
import json
import os

import pytest

from mdhub import config as cfgmod


@pytest.fixture()
def with_password(app, tmp_path):
    """给 app 配置管理员凭证（哈希存 config.json，并注入 app.config）。"""
    data_dir = os.environ["MDHUB_DATA_DIR"]
    os.makedirs(data_dir, exist_ok=True)
    cfg_path = os.path.join(data_dir, "config.json")
    cfg = {"username": "admin", "password_hash": cfgmod.hash_password("s3cret!")}
    with open(cfg_path, "w", encoding="utf-8") as f:
        json.dump(cfg, f)
    app.config["username"] = "admin"
    app.config["password_hash"] = cfg["password_hash"]
    return app


def test_login_success(client, with_password):
    r = client.post("/api/login", json={"username": "admin", "password": "s3cret!"})
    assert r.status_code == 200
    cookie = r.headers.get("Set-Cookie", "")
    assert "HttpOnly" in cookie and "SameSite=Strict" in cookie


def test_login_wrong_password_rejected(client, with_password):
    assert client.post("/api/login", json={"username": "admin", "password": "wrong"}).status_code == 401


def test_login_unknown_user_rejected(client, with_password):
    assert client.post("/api/login", json={"username": "nobody", "password": "x"}).status_code == 401


def test_login_missing_fields_400(client, with_password):
    assert client.post("/api/login", json={"username": "admin"}).status_code == 400


def test_logout_invalidates_session(client, with_password):
    client.post("/api/login", json={"username": "admin", "password": "s3cret!"})
    assert client.post("/api/logout").status_code == 200
    assert client.get("/api/me").get_json()["authenticated"] is False


def test_me_unauthenticated(client):
    assert client.get("/api/me").get_json()["authenticated"] is False


def test_me_authenticated(client, with_password):
    client.post("/api/login", json={"username": "admin", "password": "s3cret!"})
    assert client.get("/api/me").get_json()["authenticated"] is True


def test_write_endpoint_requires_auth(client, with_password):
    # 未登录访问受保护端点 → 401（占位端点，管理票继承该守卫）
    assert client.post("/api/entry", json={"path": "/tmp"}).status_code == 401


def test_write_endpoint_allowed_after_login(client, with_password):
    client.post("/api/login", json={"username": "admin", "password": "s3cret!"})
    r = client.post("/api/entry", json={"path": "/tmp"})
    assert r.status_code == 201  # 守卫放行后，索引管理业务生效（ticket 08 行为）
