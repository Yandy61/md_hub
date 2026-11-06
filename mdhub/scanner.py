"""目录扫描：递归收集 md/html 文件，排除指定目录与隐藏项。"""
import os

EXCLUDED_NAMES = {".git", ".svn", "node_modules", "__pycache__"}

# 目录索引收录的可渲染文档扩展名（小写）
DOC_EXTENSIONS = (".md", ".html", ".htm")


def is_excluded(name):
    return name in EXCLUDED_NAMES or name.startswith(".")


def is_doc_file(name):
    return name.lower().endswith(DOC_EXTENSIONS) and not is_excluded(name)


def scan_dir(root):
    """返回 root 下所有可渲染文档（md/html）的相对路径列表（POSIX 风格，排序稳定）。"""
    result = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = sorted(d for d in dirnames if not is_excluded(d))
        for fn in sorted(filenames):
            if is_doc_file(fn):
                rel = os.path.relpath(os.path.join(dirpath, fn), root)
                result.append(rel.replace(os.sep, "/"))
    return result
