"""需求3：目录选择器 /api/browse（home 为根、允许软链）。"""
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


def _root(app, tmp_path):
    root = tmp_path / "browseroot"
    root.mkdir()
    app.config["BROWSE_ROOT"] = str(root)
    return root


def test_browse_requires_auth(client, with_password):
    assert client.get("/api/browse").status_code == 401


def test_browse_lists_dirs_and_md_files(client, with_password, app, tmp_path):
    _login(client)
    root = _root(app, tmp_path)
    (root / "sub").mkdir()
    (root / "readme.md").write_text("r", encoding="utf-8")
    (root / "note.txt").write_text("t", encoding="utf-8")
    (root / ".hidden").mkdir()
    (root / ".git").mkdir()
    data = client.get("/api/browse").get_json()
    assert data["current"] == os.path.realpath(str(root))
    assert [d["name"] for d in data["dirs"]] == ["sub"]
    assert [f["name"] for f in data["files"]] == ["readme.md"]


def test_browse_symlink_allowed(client, with_password, app, tmp_path):
    _login(client)
    root = _root(app, tmp_path)
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "x.md").write_text("x", encoding="utf-8")
    os.symlink(str(outside), str(root / "link"))
    r = client.get("/api/browse", query_string={"path": str(root / "link")})
    assert r.status_code == 200
    assert r.get_json()["current"] == os.path.realpath(str(outside))


def test_browse_outside_rejected(client, with_password, app, tmp_path):
    _login(client)
    _root(app, tmp_path)
    assert client.get("/api/browse", query_string={"path": "/etc"}).status_code == 403


def test_browse_parent_via_symlink_returns_none(client, with_password, app, tmp_path):
    # 软链进入后，其真实父目录不在许可根内 → parent 为 null（防越界）
    _login(client)
    root = _root(app, tmp_path)
    outside = tmp_path / "ow"
    outside.mkdir()
    os.symlink(str(outside), str(root / "ln"))
    data = client.get("/api/browse", query_string={"path": str(root / "ln")}).get_json()
    assert data["parent"] is None