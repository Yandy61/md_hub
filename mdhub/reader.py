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


def detect_encoding(path):
    """返回文件当前编码（按 read_text 的探测顺序）；文件不存在时返回 utf-8。"""
    try:
        _, enc = read_text(path)
        return enc
    except (OSError, UnicodeDecodeError):
        return "utf-8"


def write_text(path, text):
    """写回文本：优先沿用文件原编码；原编码表不下的字符回退 UTF-8。"""
    enc = detect_encoding(path)
    try:
        data = text.encode(enc)
    except UnicodeEncodeError:
        enc = "utf-8"
        data = text.encode(enc)
    with open(path, "wb") as f:
        f.write(data)
    return enc
