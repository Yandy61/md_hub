"""文档读取：UTF-8 为主，GBK 自动兜底。"""
_ENCODINGS = ("utf-8", "gbk")


def read_text(path):
    """返回 (text, encoding)。无法解码时抛 UnicodeDecodeError。"""
    with open(path, "rb") as f:
        raw = f.read()
    last_err = None
    for enc in _ENCODINGS:
        try:
            return raw.decode(enc), enc
        except UnicodeDecodeError as e:
            last_err = e
    raise last_err
