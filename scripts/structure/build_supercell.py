"""按三个正整数倍数扩胞，按元素排序并写入 VASP Direct 坐标（依赖 ASE）。

用法：python build_supercell.py POSCAR 2 2 1 [-o supercell.vasp]
默认输出在输入文件所在目录，名称为输入文件主名_SC221.vasp；已有输出不会覆盖。
"""

import argparse
import os
import tempfile
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument(
        "repeat", nargs=3, type=int, metavar="N", help="a、b、c 方向扩胞倍数"
    )
    parser.add_argument("-o", "--output", type=Path)
    args = parser.parse_args()
    if any(n <= 0 for n in args.repeat):
        parser.error("扩胞倍数必须为正整数")
    if not args.input.is_file():
        parser.error(f"输入文件不存在：{args.input}")
    output = args.output or args.input.with_name(
        f"{args.input.stem}_SC{''.join(map(str, args.repeat))}.vasp"
    )
    if output.exists() or output.is_symlink():
        parser.error(f"输出已存在：{output}")
    if not output.parent.is_dir():
        parser.error(f"输出目录不存在：{output.parent}")
    from ase.build import sort
    from ase.io import read, write

    try:
        structure = sort(read(args.input).repeat(args.repeat))
        # 明确格式，支持用户指定无 .vasp 扩展名的输出。
        with tempfile.NamedTemporaryFile(mode="w", dir=output.parent) as stream:
            write(stream, structure, format="vasp", direct=True)
            stream.flush()
            # 同目录硬链接原子发布，已有目标不会被覆盖。
            os.link(stream.name, output)
    except (OSError, ValueError, RuntimeError) as error:
        parser.exit(1, f"错误：{error}\n")
    print(f"超胞结构已保存为：{output}")


if __name__ == "__main__":
    main()
