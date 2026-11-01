"""CP2K 区块读写辅助，供 cp2k_restart.py 和 diag2ot_geo2cell2md.py 调用。

按完整区块路径匹配，忽略注释和大小写；不使用跨区块的贪婪文本替换。
"""

import re


def spans(text, path):
    lines = text.splitlines(keepends=True)
    stack, found = [], []
    wanted = tuple(name.upper() for name in path)
    for index, line in enumerate(lines):
        code = re.split(r"[!#]", line, maxsplit=1)[0].strip().upper()
        if not code.startswith("&"):
            continue
        tokens = code[1:].split()
        if not tokens:
            continue
        if tokens[0] == "END":
            if not stack:
                raise ValueError("发现没有起始区块的 &END")
            name, start = stack[-1]
            if len(tokens) > 1 and tokens[1] != name:
                raise ValueError(f"区块闭合不匹配：{name} / {tokens[1]}")
            names = tuple(item[0] for item in stack)
            if names == wanted:
                found.append((start, index + 1))
            stack.pop()
        else:
            stack.append((tokens[0], index))
    if stack:
        raise ValueError("输入文件有未闭合区块")
    return lines, found


def section(text, path):
    lines, found = spans(text, path)
    if len(found) != 1:
        raise ValueError(f"区块 {'/'.join(path)} 应唯一，实际为 {len(found)} 个")
    start, end = found[0]
    return "".join(lines[start:end])


def replace_section(text, path, replacement):
    lines, found = spans(text, path)
    if len(found) != 1:
        raise ValueError(f"无法唯一定位 {'/'.join(path)}")
    start, end = found[0]
    return "".join(lines[:start]) + replacement.rstrip() + "\n" + "".join(lines[end:])


def insert_section(text, parent, replacement):
    lines, found = spans(text, parent)
    if len(found) != 1:
        raise ValueError(f"无法唯一定位父区块 {'/'.join(parent)}")
    _, end = found[0]
    return (
        "".join(lines[: end - 1])
        + replacement.rstrip()
        + "\n"
        + "".join(lines[end - 1 :])
    )


def keyword(text, path, name):
    block = section(text, path)
    depth = 0
    values = []
    for line in block.splitlines():
        code = re.split(r"[!#]", line, maxsplit=1)[0].strip()
        if code.startswith("&"):
            depth += -1 if code[1:].upper().startswith("END") else 1
        elif depth == 1:
            tokens = code.split()
            if tokens and tokens[0].upper() == name.upper():
                values.append(" ".join(tokens[1:]))
    if len(values) > 1:
        raise ValueError(f"关键字 {name} 重复")
    return values[0] if values else None


def set_keyword(text, path, name, value):
    block = section(text, path)
    lines, depth, result = block.splitlines(), 0, []
    for line in lines:
        code = re.split(r"[!#]", line, maxsplit=1)[0].strip()
        if code.startswith("&"):
            depth += -1 if code[1:].upper().startswith("END") else 1
        elif depth == 1 and code.split() and code.split()[0].upper() == name.upper():
            continue
        result.append(line)
    if value is not None:
        result.insert(len(result) - 1, f"  {name.upper()} {value}")
    return replace_section(text, path, "\n".join(result))
