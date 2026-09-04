"""写回前的备份：项目侧 .backups/ 时间戳文件，保留最近 N 份。"""
import datetime
import glob
import os
import re


def backup_file(path, backup_dir, keep=10):
    """把 path 当前内容备份到 backup_dir，返回备份文件路径。超出 keep 份删最旧。"""
    os.makedirs(backup_dir, exist_ok=True)
    digest = re.sub(r"[^A-Za-z0-9_.-]", "_", os.path.abspath(path)).strip("_")[-80:]
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
