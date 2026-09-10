"""需求1：字母 id（随机 8 位大小写字母）与注册表迁移。"""
import json
import os
import re

import pytest

from mdhub.registry import Registry

ID_RE = re.compile(r"^[A-Za-z]{8}$")


def test_add_generates_alphabetic_id(tmp_path):
    p = tmp_path / "a.md"
    p.write_text("a", encoding="utf-8")
    reg = Registry(str(tmp_path / "registry.json"))
    e = reg.add(str(p), "file")
    assert ID_RE.match(e["id"])


def test_add_idempotent_same_id(tmp_path):
    p = tmp_path / "b.md"
    p.write_text("b", encoding="utf-8")
    reg = Registry(str(tmp_path / "registry.json"))
    e1 = reg.add(str(p), "file")
    e2 = reg.add(str(p), "file")
    assert e1["id"] == e2["id"]


def test_add_ids_unique(tmp_path):
    reg = Registry(str(tmp_path / "registry.json"))
    ids = set()
    for i in range(50):
        p = tmp_path / f"c{i}.md"
        p.write_text("x", encoding="utf-8")
        ids.add(reg.add(str(p), "file")["id"])
    assert len(ids) == 50


def test_migrate_converts_numeric_ids_and_drops_next_id(tmp_path):
    reg_path = str(tmp_path / "registry.json")
    # 模拟旧版数字 id 注册表（含 next_id）
    with open(reg_path, "w", encoding="utf-8") as f:
        json.dump({
            "next_id": 9,
            "entries": [
                {"id": "3", "path": "/tmp/x.md", "type": "file", "created_in_service": False},
                {"id": "4", "path": "/tmp/y.md", "type": "file", "created_in_service": False},
            ],
        }, f)
    reg = Registry(reg_path)  # __init__ 触发幂等迁移
    entries = reg.entries()
    ids = [e["id"] for e in entries]
    assert all(ID_RE.match(i) for i in ids)
    assert len(set(ids)) == 2
    # 已写回文件且 next_id 被剔除
    with open(reg_path, encoding="utf-8") as f:
        data = json.load(f)
    assert "next_id" not in data
    assert all(ID_RE.match(e["id"]) for e in data["entries"])


def test_migrate_idempotent(tmp_path):
    reg_path = str(tmp_path / "registry.json")
    p = tmp_path / "d.md"
    p.write_text("d", encoding="utf-8")
    reg = Registry(reg_path)
    e = reg.add(str(p), "file")
    # 再次实例化（模拟重启）不应改变已合法的字母 id
    reg2 = Registry(reg_path)
    entries = reg2.entries()
    assert entries[0]["id"] == e["id"]