"""提取 XDATCAR 帧（依赖 ASE）。

用法：python xdatcar_slice.py XDATCAR 0 100 10 -o XDATCAR_REV
索引从零开始，包含 begin、不包含 end，step 为采样间隔。
"""

import argparse
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("begin", type=int)
    parser.add_argument("end", type=int)
    parser.add_argument("step", type=int, nargs="?", default=1)
    parser.add_argument("-o", "--output", type=Path, default=Path("XDATCAR_REV"))
    args = parser.parse_args()
    if args.step <= 0 or args.begin < 0 or args.end <= args.begin:
        parser.error("须满足 0 <= begin < end 且 step > 0")
    if args.output.exists():
        parser.error("输出文件已存在")
    from ase.io import read, write

    images = read(
        args.input, format="vasp-xdatcar", index=f"{args.begin}:{args.end}:{args.step}"
    )
    if not images:
        parser.error("选中的轨迹为空")
    write(args.output, images, format="vasp-xdatcar")
    print(f"已提取 {len(images)} 帧")


if __name__ == "__main__":
    main()
