"""写回前的备份：项目侧 .backups/ 时间戳文件，保留最近 N 份。"""
import datetime
import glob
import hashlib
import os


def backup_file(path, backup_dir, keep=10):
    """把 path 当前内容备份到 backup_dir，返回备份文件路径。超出 keep 份删最旧。"""
    os.makedirs(backup_dir, exist_ok=True)
    # sha1(abspath) 前 16 位做 key：不同路径不碰撞，同一路径稳定
    digest = hashlib.sha1(os.path.abspath(path).encode("utf-8")).hexdigest()[:16]
    stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    dest = os.path.join(backup_dir, f"{digest}.{stamp}.bak")
    with open(path, "rb") as src, open(dest, "wb") as dst:
        dst.write(src.read())
    _rotate(backup_dir, digest, keep)
    return dest


def _rotate(backup_dir, digest, keep):
    pattern = os.path.join(backup_dir, f"{digest}.*.bak")
    files = sorted(glob.glob(pattern))
    for old in files[:-keep] if keep > 0 else []:
        try:
            os.remove(old)
        except OSError:
            pass
