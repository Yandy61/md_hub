"""ticket 05：轮询实时刷新的数据源行为。"""
import json
import os
import shutil
import time

import pytest


def _add_dir(client_app, path):
    from mdhub.registry import Registry

    return Registry(client_app.config["REGISTRY_PATH"]).add(str(path), "dir")


@pytest.fixture()
def polltree(tmp_path):
    root = tmp_path / "poll"
    root.mkdir()
    (root / "a.md").write_text("A", encoding="utf-8")
    return root


def test_list_reflects_new_file(client, app, polltree):
    entry = _add_dir(app, polltree)
    (polltree / "new.md").write_text("N", encoding="utf-8")
    files = _files(client, entry["id"])
    assert "new.md" in [f["rel"] for f in files]


def test_list_reflects_deleted_file(client, app, polltree):
    entry = _add_dir(app, polltree)
    (polltree / "new.md").write_text("N", encoding="utf-8")
    _files(client, entry["id"])  # 第一次看到
    os.remove(polltree / "new.md")
    files = _files(client, entry["id"])
    assert "new.md" not in [f["rel"] for f in files]


def test_doc_mtime_changes_on_edit(client, app, tmp_path):
    from mdhub.registry import Registry

    p = tmp_path / "m.md"
    p.write_text("v1", encoding="utf-8")
    entry = Registry(app.config["REGISTRY_PATH"]).add(str(p), "file")
    d1 = client.get(f"/api/doc/{entry['id']}/").get_json()
    time.sleep(0.02)
    p.write_text("v2 longer content", encoding="utf-8")
    d2 = client.get(f"/api/doc/{entry['id']}/").get_json()
    assert (d2["mtime"], d2["size"]) != (d1["mtime"], d1["size"])
    assert d2["text"] == "v2 longer content"


def test_entry_reappears_after_restore(client, app, polltree):
    entry = _add_dir(app, polltree)
    shutil.rmtree(str(polltree))
    e = _entry(client, entry["id"])
    assert e["missing"] is True
    polltree.mkdir()
    (polltree / "a.md").write_text("A", encoding="utf-8")
    e = _entry(client, entry["id"])
    assert e["missing"] is False
    assert [f["rel"] for f in e["files"]] == ["a.md"]


def _files(client, eid):
    return _entry(client, eid)["files"]


def _entry(client, eid):
    entries = client.get("/api/list").get_json()["entries"]
    return next(x for x in entries if x["id"] == eid)
