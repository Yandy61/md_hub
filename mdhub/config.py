"""MarkdownHub 服务配置与路径约定。

所有运行期可变状态集中在一个数据目录下（默认 <项目>/data），
config.json 只存配置与凭证哈希，registry.json 存索引条目。
"""
import hashlib
import json
import os
import secrets

PROJECT_ROOT = os.path.dirname(os.path.abspath(os.path.dirname(__file__)))
DATA_DIR = os.environ.get("MDHUB_DATA_DIR") or os.path.join(PROJECT_ROOT, "data")
CONFIG_PATH = os.path.join(DATA_DIR, "config.json")
REGISTRY_PATH = os.path.join(DATA_DIR, "registry.json")
WORKSPACE_DIR = os.path.join(PROJECT_ROOT, "workspace")
BACKUP_DIR = os.path.join(PROJECT_ROOT, "data", "backups")
LOG_DIR = os.path.join(PROJECT_ROOT, "logs")

DEFAULT_CONFIG = {
    "host": "0.0.0.0",
    "port": 18123,
    "workspace": WORKSPACE_DIR,
    "backup_keep": 10,
    "username": "admin",
    "password_hash": None,
    "secret_key": None,
}


def load_config(path=CONFIG_PATH):
    cfg = dict(DEFAULT_CONFIG)
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            cfg.update(json.load(f))
    if not cfg.get("secret_key"):
        cfg["secret_key"] = secrets.token_hex(32)
    return cfg


def hash_password(password, salt=None):
    salt = salt or secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 100_000)
    return f"pbkdf2${salt}${digest.hex()}"


def verify_password(password, stored):
    if not stored:
        return False
    try:
        _, salt, digest = stored.split("$")
    except ValueError:
        return False
    check = hash_password(password, salt)
    return secrets.compare_digest(check, stored)


def atomic_write_json(path, obj):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)
    os.replace(tmp, path)


def set_password(username, password, path=CONFIG_PATH):
    """设置管理员凭证（PBKDF2 哈希 + 随机 session 密钥），写入 config.json。"""
    cfg = load_config(path)
    cfg["username"] = username
    cfg["password_hash"] = hash_password(password)
    cfg["secret_key"] = secrets.token_hex(32)  # 换密后旧会话全部失效
    atomic_write_json(path, cfg)
    return cfg
