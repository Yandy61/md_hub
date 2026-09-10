import os
import sys

# 保证 mdhub 包可导入（pytest 不自动把 rootdir 加进 sys.path）
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import importlib

import pytest


@pytest.fixture()
def app(tmp_path, monkeypatch):
    """隔离环境中的 Flask app：临时数据目录、无密码、guest 模式。"""
    monkeypatch.setenv("MDHUB_DATA_DIR", str(tmp_path / "data"))
    # 每次用例重新加载模块，保证路径常量指向临时目录
    for mod in [m for m in list(sys.modules) if m == "mdhub" or m.startswith("mdhub.")]:
        del sys.modules[mod]
    import mdhub.app as app_module
    importlib.reload(app_module)
    return app_module.create_app()


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def with_password(app, tmp_path):
    """写入管理员凭证到 config.json（供登录类测试）。"""
    import json

    from mdhub import config as cfgmod

    data_dir = os.environ["MDHUB_DATA_DIR"]
    os.makedirs(data_dir, exist_ok=True)
    cfg = {"username": "admin", "password_hash": cfgmod.hash_password("s3cret!")}
    with open(os.path.join(data_dir, "config.json"), "w", encoding="utf-8") as f:
        json.dump(cfg, f)
    return app


@pytest.fixture()
def login(client, with_password):
    """已登录的 test client（与 client 同一实例，注入 session）。"""
    client.post("/api/login", json={"username": "admin", "password": "s3cret!"})
    return client
