"""将重启文件的结构写入 CP2K 输入。用法：python apply_cp2k_restart.py restart.inp input.inp -o continued.inp。

默认生成新文件；--in-place 才原地修改，同时保留 input.inp.bak。
MD→MD 时也复制 MOTION/MD 和速度；其他情况保留目标任务类型。
"""

import argparse
import os
import shutil
import tempfile
from pathlib import Path

from cp2k_sections import (
    insert_section,
    keyword,
    replace_section,
    section,
    set_keyword,
    spans,
)


def apply_restart(restart, target):
    subsys = ("FORCE_EVAL", "SUBSYS")
    for name in ("CELL", "COORD"):
        path = subsys + (name,)
        target = replace_section(target, path, section(restart, path))
    source_type = (keyword(restart, ("GLOBAL",), "RUN_TYPE") or "").upper()
    target_type = (keyword(target, ("GLOBAL",), "RUN_TYPE") or "").upper()
    if source_type == target_type == "MD":
        target = replace_section(
            target, ("MOTION", "MD"), section(restart, ("MOTION", "MD"))
        )
        path = subsys + ("VELOCITY",)
        velocity = section(restart, path)
        if spans(target, path)[1]:
            target = replace_section(target, path, velocity)
        else:
            target = insert_section(target, subsys, velocity)
    elif source_type != "MD" and target_type != "MD":
        for mode in ("GEO_OPT", "CELL_OPT"):
            path = ("MOTION", mode)
            if spans(restart, path)[1] and spans(target, path)[1]:
                value = keyword(restart, path, "STEP_START_VAL")
                if value is not None:
                    target = set_keyword(target, path, "STEP_START_VAL", value)
    return target


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("restart", type=Path)
    parser.add_argument("input", type=Path)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("-o", "--output", type=Path)
    mode.add_argument("--in-place", action="store_true")
    args = parser.parse_args()
    output = (
        args.input
        if args.in_place
        else args.output or args.input.with_suffix(".continued.inp")
    )
    backup = args.input.with_name(args.input.name + ".bak")
    try:
        if (not args.in_place and (output.exists() or output.is_symlink())) or (
            args.in_place and (backup.exists() or backup.is_symlink())
        ):
            raise FileExistsError("输出或备份文件已存在")
        if args.in_place and args.input.is_symlink():
            raise ValueError("原地更新不接受软链接输入，请使用实体文件或另选输出")
        result = apply_restart(args.restart.read_text(), args.input.read_text())
        if args.in_place:
            shutil.copy2(args.input, backup)
        with tempfile.NamedTemporaryFile(
            mode="w", dir=output.parent, delete=False
        ) as stream:
            temporary = Path(stream.name)
            try:
                stream.write(result)
                stream.flush()
                if args.in_place:
                    shutil.copymode(args.input, temporary)
                    os.replace(temporary, output)
                else:
                    os.link(temporary, output)
            finally:
                temporary.unlink(missing_ok=True)
    except (ValueError, OSError) as error:
        parser.exit(1, f"错误：{error}\n")
    print(output)


if __name__ == "__main__":
    main()
