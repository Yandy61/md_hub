"""ticket 04：相对资源服务边界。"""
import os

import pytest


def _add_dir(client_app, path):
    from mdhub.registry import Registry

    return Registry(client_app.config["REGISTRY_PATH"]).add(str(path), "dir")


def _add_file(client_app, path):
    from mdhub.registry import Registry

    return Registry(client_app.config["REGISTRY_PATH"]).add(str(path), "file")


@pytest.fixture()
def asset_tree(tmp_path):
    """docs/ 树：md 与图片混排。"""
    root = tmp_path / "assets"
    (root / "img").mkdir(parents=True)
    (root / "a.md").write_text("![x](./img/a.png)", encoding="utf-8")
    (root / "img" / "a.png").write_bytes(b"\x89PNG fake")
    return root


def test_dir_entry_serves_subtree_asset(client, app, asset_tree):
    entry = _add_dir(app, asset_tree)
    r = client.get(f"/api/asset/{entry['id']}/img/a.png")
    assert r.status_code == 200
    assert r.data == b"\x89PNG fake"


def test_file_entry_serves_sibling_asset(client, app, tmp_path):
    d = tmp_path / "sibs"
    d.mkdir()
    (d / "note.md").write_text("see img", encoding="utf-8")
    (d / "pic.jpg").write_bytes(b"jpegdata")
    entry = _add_file(app, d / "note.md")
    r = client.get(f"/api/asset/{entry['id']}/pic.jpg")
    assert r.status_code == 200
    assert r.data == b"jpegdata"


def test_asset_traversal_blocked(client, app, tmp_path):
    d = tmp_path / "t"
    d.mkdir()
    (d / "m.md").write_text("m", encoding="utf-8")
    (d.parent / "outside.png").write_bytes(b"secret")
    entry = _add_dir(app, d)
    assert client.get(f"/api/asset/{entry['id']}/../outside.png").status_code == 404


def test_file_entry_asset_beyond_sibling_blocked(client, app, tmp_path):
    d = tmp_path / "s2"
    d.mkdir()
    (d / "n.md").write_text("n", encoding="utf-8")
    (d.parent / "far.png").write_bytes(b"x")
    entry = _add_file(app, d / "n.md")
    # 单文件索引：同目录外不可达
    assert client.get(f"/api/asset/{entry['id']}/../far.png").status_code == 404


def test_asset_unknown_or_nonexistent_404(client, app, asset_tree):
    entry = _add_dir(app, asset_tree)
    assert client.get(f"/api/asset/{entry['id']}/img/nope.png").status_code == 404
    assert client.get("/api/asset/999/x.png").status_code == 404


def test_asset_dirs_listing_not_served(client, app, asset_tree):
    # 目录本身不是资产
    entry = _add_dir(app, asset_tree)
    assert client.get(f"/api/asset/{entry['id']}/img").status_code == 404
