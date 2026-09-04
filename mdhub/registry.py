"""registry：索引条目的存储层（JSON 原子写）。"""
import datetime
import os

from mdhub import config


class Registry:
    def __init__(self, path=config.REGISTRY_PATH):
        self.path = path

    def _load(self):
        if os.path.exists(self.path):
            with open(self.path, "r", encoding="utf-8") as f:
                return json_load(f)
        return {"next_id": 1, "entries": []}

    def save(self, data):
        config.atomic_write_json(self.path, data)

    def add(self, path, type_):
        path = os.path.abspath(path)
        if not os.path.exists(path):
            raise FileNotFoundError(path)
        data = self._load()
        # 同一路径重复索引 → 返回已有条目（幂等）
        for e in data["entries"]:
            if e["path"] == path:
                return e
        entry = {
            "id": str(data["next_id"]),
            "path": path,
            "type": type_,
            "added_at": datetime.datetime.now().isoformat(timespec="seconds"),
        }
        data["next_id"] += 1
        data["entries"].append(entry)
        self.save(data)
        return entry

    def remove(self, entry_id):
        data = self._load()
        before = len(data["entries"])
        data["entries"] = [e for e in data["entries"] if e["id"] != entry_id]
        if len(data["entries"]) == before:
            return False
        self.save(data)
        return True

    def entries(self):
        return self._load()["entries"]


def json_load(f):
    import json

    return json.load(f)
