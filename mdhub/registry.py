"""registry：索引条目的存储层（JSON 原子写 + 线程锁）。"""
import datetime
import json
import os
import threading

from mdhub import config


class Registry:
    def __init__(self, path=config.REGISTRY_PATH):
        self.path = path
        self._lock = threading.Lock()

    def _load_unlocked(self):
        if os.path.exists(self.path):
            with open(self.path, "r", encoding="utf-8") as f:
                return json.load(f)
        return {"next_id": 1, "entries": []}

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
            entry = {
                "id": str(data["next_id"]),
                "path": path,
                "type": type_,
                "created_in_service": created_in_service,
                "added_at": datetime.datetime.now().isoformat(timespec="seconds"),
            }
            data["next_id"] += 1
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
