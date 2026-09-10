"""registry：索引条目的存储层（JSON 原子写 + 线程锁）。

条目 id 为随机 8 位大小写字母串（防反推枚举）；旧版数字 id 在首次实例化时幂等迁移。
"""
import datetime
import json
import os
import secrets
import string
import threading

from mdhub import config


def is_valid_id(cid):
    """id 必须是 8 位仅大小写字母的字符串。"""
    return isinstance(cid, str) and len(cid) == 8 and all(c in string.ascii_letters for c in cid)


class Registry:
    def __init__(self, path=config.REGISTRY_PATH):
        self.path = path
        self._lock = threading.Lock()
        self._migrate()

    def _load_unlocked(self):
        if os.path.exists(self.path):
            with open(self.path, "r", encoding="utf-8") as f:
                return json.load(f)
        return {"entries": []}

    def _new_id(self, used):
        while True:
            cid = "".join(secrets.choice(string.ascii_letters) for _ in range(8))
            if cid not in used:
                return cid

    def _migrate(self):
        """幂等：把非字母 id 迁移为随机字母 id，剔除 next_id 字段。"""
        with self._lock:
            data = self._load_unlocked()
            entries = data.get("entries", [])
            changed = "next_id" in data
            used = set()
            for e in entries:
                if not is_valid_id(e.get("id")) or e["id"] in used:
                    e["id"] = self._new_id(used)
                    changed = True
                used.add(e["id"])
            if "next_id" in data:
                del data["next_id"]
            if changed:
                config.atomic_write_json(self.path, data)

    def add(self, path, type_, created_in_service=False):
        path = os.path.abspath(path)
        if not os.path.exists(path):
            raise FileNotFoundError(path)
        with self._lock:
            data = self._load_unlocked()
            # 同一路径重复索引 → 返回已有条目（幂等）
            for e in data["entries"]:
                if e["path"] == path:
                    return e
            used = {e["id"] for e in data["entries"]}
            entry = {
                "id": self._new_id(used),
                "path": path,
                "type": type_,
                "created_in_service": created_in_service,
                "added_at": datetime.datetime.now().isoformat(timespec="seconds"),
            }
            data["entries"].append(entry)
            config.atomic_write_json(self.path, data)
            return entry

    def remove(self, entry_id):
        with self._lock:
            data = self._load_unlocked()
            before = len(data["entries"])
            data["entries"] = [e for e in data["entries"] if e["id"] != entry_id]
            if len(data["entries"]) == before:
                return False
            config.atomic_write_json(self.path, data)
            return True

    def entries(self):
        with self._lock:
            return self._load_unlocked()["entries"]