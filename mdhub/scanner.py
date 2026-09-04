"""目录扫描：递归收集 md 文件，排除指定目录与隐藏项。"""
import os

EXCLUDED_NAMES = {".git", ".svn", "node_modules", "__pycache__"}


def is_excluded(name):
    return name in EXCLUDED_NAMES or name.startswith(".")


def scan_dir(root):
    """返回 root 下所有 md 文件的相对路径列表（POSIX 风格，排序稳定）。"""
    result = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = sorted(d for d in dirnames if not is_excluded(d))
        for fn in sorted(filenames):
            if fn.endswith(".md") and not is_excluded(fn):
                rel = os.path.relpath(os.path.join(dirpath, fn), root)
                result.append(rel.replace(os.sep, "/"))
    return result
