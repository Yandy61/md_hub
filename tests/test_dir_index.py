import os

import pytest


@pytest.fixture()
def dirtree(tmp_path):
    """建一棵含排除项的目录树：
    root/
      a.md  sub/b.md  sub/deep/c.md  .hidden.md  node_modules/x.md  .git/y.md  note.txt
    """
    root = tmp_path / "docsroot"
    (root / "sub" / "deep").mkdir(parents=True)
    (root / "node_modules").mkdir()
    (root / ".git").mkdir()
    (root / "a.md").write_text("A", encoding="utf-8")
    (root / "sub" / "b.md").write_text("B", encoding="utf-8")
    (root / "sub" / "deep" / "c.md").write_text("C", encoding="utf-8")
    (root / ".hidden.md").write_text("H", encoding="utf-8")
    (root / "node_modules" / "x.md").write_text("X", encoding="utf-8")
    (root / ".git" / "y.md").write_text("Y", encoding="utf-8")
    (root / "note.txt").write_text("t", encoding="utf-8")
    return str(root)


@pytest.fixture()
def dir_entry(client, app, dirtree):
    from mdhub.registry import Registry

    return Registry(app.config["REGISTRY_PATH"]).add(dirtree, "dir")


def test_dir_list_recursive(client, dir_entry):
    e = _entry(client, dir_entry["id"])
    rels = [f["rel"] for f in e["files"]]
    assert rels == ["a.md", "sub/b.md", "sub/deep/c.md"]
    for f in e["files"]:
        assert "mtime" in f and "size" in f


def _entry(client, eid):
    entries = client.get("/api/list").get_json()["entries"]
    return next(x for x in entries if x["id"] == eid)


def test_dir_list_exclusions(client, dir_entry):
    e = _entry(client, dir_entry["id"])
    joined = " ".join(f["rel"] for f in e["files"])
    for bad in ["hidden", "node_modules", ".git", "note.txt"]:
        assert bad not in joined


def test_dir_missing_marked(client, app, tmp_path):
    from mdhub.registry import Registry

    d = tmp_path / "gone"
    d.mkdir()
    (d / "x.md").write_text("x", encoding="utf-8")
    entry = Registry(app.config["REGISTRY_PATH"]).add(str(d), "dir")
    import shutil

    shutil.rmtree(str(d))
    e = _entry(client, entry["id"])
    assert e["missing"] is True
    assert e["files"] == []


def test_dir_doc_by_relpath(client, dir_entry):
    r = client.get(f"/api/doc/{dir_entry['id']}/sub/b.md")
    assert r.status_code == 200
    assert r.get_json()["text"] == "B"


def test_dir_doc_outside_root_blocked(client, app, tmp_path, dir_entry):
    # 根目录外的文件不可达
    secret = tmp_path / "sibling_secret.md"
    secret.write_text("s", encoding="utf-8")
    r = client.get(f"/api/doc/{dir_entry['id']}/../sibling_secret.md")
    assert r.status_code == 404


def test_file_entry_subpath_rejected(client, app, tmp_path):
    from mdhub.registry import Registry

    p = tmp_path / "s.md"
    p.write_text("s", encoding="utf-8")
    entry = Registry(app.config["REGISTRY_PATH"]).add(str(p), "file")
    assert client.get(f"/api/doc/{entry['id']}/x.md").status_code == 404
