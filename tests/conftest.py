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
