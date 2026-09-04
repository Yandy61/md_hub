import json
import os

import pytest

os.environ.setdefault("MDHUB_DATA_DIR", "")


@pytest.fixture()
def app(tmp_path, monkeypatch):
    """隔离环境中的 Flask app：临时数据目录、无密码、guest 模式。"""
    monkeypatch.setenv("MDHUB_DATA_DIR", str(tmp_path / "data"))
    # 每次用例重新导入 app 模块，保证路径常量指向临时目录
    import importlib
    import sys
    for mod in [m for m in sys.modules if m == "mdhub.app" or m.startswith("mdhub.app")]:
        del sys.modules[mod]
    import mdhub.app as app_module
    importlib.reload(app_module)
    return app_module.create_app()


@pytest.fixture()
def client(app):
    return app.test_client()


def test_health(client):
    r = client.get("/api/health")
    assert r.status_code == 200
    assert r.get_json()["status"] == "ok"
