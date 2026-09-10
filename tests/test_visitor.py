import json
import os

import pytest


@pytest.fixture()
def mdfile(tmp_path):
    p = tmp_path / "hello.md"
    p.write_text("# 你好\n\n正文 **加粗**\n", encoding="utf-8")
    return str(p)


@pytest.fixture()
def indexed_file(client, mdfile, app):
    """通过 registry 直接放置一条单文件索引（管理 API 属于 ticket 08）。"""
    from mdhub.registry import Registry

    reg = Registry(app.config["REGISTRY_PATH"])
    entry = reg.add(mdfile, "file")
    return entry


def test_list_shows_indexed_file(client, indexed_file, mdfile, login):
    r = client.get("/api/list")
    assert r.status_code == 200
    entries = r.get_json()["entries"]
    assert len(entries) == 1
    e = entries[0]
    assert e["path"] == os.path.abspath(mdfile)
    assert e["type"] == "file"
    assert e["missing"] is False


def test_doc_returns_raw_markdown(client, indexed_file):
    r = client.get(f"/api/doc/{indexed_file['id']}/")
    assert r.status_code == 200
    body = r.get_json()
    assert body["text"].startswith("# 你好")
    assert body["encoding"] == "utf-8"
    assert "mtime" in body and "size" in body


def test_doc_gbk_fallback(client, app, tmp_path):
    from mdhub.registry import Registry

    p = tmp_path / "gbk.md"
    p.write_bytes("中文编码测试\n".encode("gbk"))
    reg = Registry(app.config["REGISTRY_PATH"])
    entry = reg.add(str(p), "file")
    r = client.get(f"/api/doc/{entry['id']}/")
    assert r.get_json()["encoding"] == "gbk"
    assert "中文编码测试" in r.get_json()["text"]


def test_doc_unknown_entry_404(client):
    assert client.get("/api/doc/999/").status_code == 404


def test_doc_traversal_blocked(client, indexed_file):
    r = client.get(f"/api/doc/{indexed_file['id']}/../secrets.txt")
    assert r.status_code == 404


def test_missing_source_marked(client, indexed_file, tmp_path, login):
    # 源文件被外部删除 → 条目保留并标记 missing
    os.remove(indexed_file["path"])
    r = client.get("/api/list")
    e = r.get_json()["entries"][0]
    assert e["missing"] is True
    assert client.get(f"/api/doc/{e['id']}/").status_code == 404


def test_index_requires_login_doc_anonymous(client, indexed_file):
    # 未登录：主界面是登录页；文档页仍匿名可达（私密链接语义）
    home = client.get("/")
    assert home.status_code == 200
    assert b"login-form" in home.data
    doc = client.get(f"/doc/{indexed_file['id']}/")
    assert doc.status_code == 200
    assert client.get(f"/api/doc/{indexed_file['id']}/").status_code == 200
    assert client.get("/api/list").status_code == 401


def test_registry_atomic_and_idempotent(app, mdfile):
    from mdhub.registry import Registry

    reg = Registry(app.config["REGISTRY_PATH"])
    e1 = reg.add(mdfile, "file")
    e2 = reg.add(mdfile, "file")
    assert e1["id"] == e2["id"]
    with open(reg.path) as f:
        data = json.load(f)
    assert len(data["entries"]) == 1


def test_pages_served(client, indexed_file):
    # 列表页与文档页均可访问，且引用本地打包资产（无 CDN）
    for url in ["/", f"/doc/{indexed_file['id']}/"]:
        r = client.get(url)
        assert r.status_code == 200
        assert b"MarkdownHub" in r.data
    assert b"cdn" not in client.get("/").data.lower()


def test_vendor_assets_served(client):
    for url in ["/static/vendor/markdown-it.min.js", "/static/vendor/highlight.min.js",
                "/static/vendor/hljs-github.css", "/static/css/mdhub.css",
                "/static/js/render.js", "/static/js/list.js", "/static/js/doc.js"]:
        assert client.get(url).status_code == 200, url
