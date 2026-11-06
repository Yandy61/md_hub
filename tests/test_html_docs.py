"""HTML 文档渲染支持：目录扫描收录 .html/.htm，doc API 正常返回。"""
import os

import pytest


@pytest.fixture(autouse=True)
def _authed(login):
    """列表断言需登录态。"""


def test_scan_dir_includes_html(tmp_path):
    from mdhub.scanner import scan_dir

    root = tmp_path / "web"
    root.mkdir()
    (root / "index.html").write_text("<h1>页面</h1>", encoding="utf-8")
    (root / "sub").mkdir()
    (root / "sub" / "report.htm").write_text("<p>x</p>", encoding="utf-8")
    (root / "a.md").write_text("A", encoding="utf-8")
    (root / "style.css").write_text("body{}", encoding="utf-8")
    (root / ".hidden.html").write_text("h", encoding="utf-8")
    rels = scan_dir(str(root))
    assert rels == ["a.md", "index.html", "sub/report.htm"]


def test_doc_api_serves_html(client, app, tmp_path):
    from mdhub.registry import Registry

    p = tmp_path / "page.html"
    p.write_text("<html><body><h1>HTML 页面</h1></body></html>", encoding="utf-8")
    entry = Registry(app.config["REGISTRY_PATH"]).add(str(p), "file")
    r = client.get(f"/api/doc/{entry['id']}/")
    assert r.status_code == 200
    assert "HTML 页面" in r.get_json()["text"]


def test_dir_entry_html_doc_by_relpath(client, app, tmp_path):
    from mdhub.registry import Registry

    d = tmp_path / "site"
    d.mkdir()
    (d / "index.html").write_text("<p>站点首页</p>", encoding="utf-8")
    entry = Registry(app.config["REGISTRY_PATH"]).add(str(d), "dir")
    r = client.get(f"/api/doc/{entry['id']}/index.html")
    assert r.status_code == 200
    assert "站点首页" in r.get_json()["text"]


def test_html_assets_served_within_boundary(client, app, tmp_path):
    """HTML 页面引用的同目录 CSS/JS/图片经资源端点可达。"""
    from mdhub.registry import Registry

    d = tmp_path / "site2"
    d.mkdir()
    (d / "page.html").write_text(
        '<link rel="stylesheet" href="style.css">', encoding="utf-8")
    (d / "style.css").write_text("body{color:red}", encoding="utf-8")
    entry = Registry(app.config["REGISTRY_PATH"]).add(str(d), "dir")
    assert client.get(f"/api/asset/{entry['id']}/style.css").status_code == 200
    # .html 同目录相对链接仍不可越界
    assert client.get(f"/api/asset/{entry['id']}/../outside.css").status_code == 404