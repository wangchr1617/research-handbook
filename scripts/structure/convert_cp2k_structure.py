"""用 Multiwfn 转换 CP2K 重启结构，不执行计算。

用法：python convert_cp2k_structure.py cp2k-1.restart --format cif --output-dir converted
输出目录必须不存在；依赖 Multiwfn，实际文件名由该程序决定。
"""

import argparse
import subprocess
from pathlib import Path

FORMAT_CODES = {"vasp": 27, "cif": 33, "pdb": 1, "xyz": 2}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("--format", choices=FORMAT_CODES, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--executable", default="Multiwfn")
    args = parser.parse_args()
    if not args.input.is_file() or args.output_dir.exists():
        parser.error("输入不存在或输出目录已存在")
    args.output_dir.mkdir(parents=True)
    commands = f"{args.input.resolve()}\n100\n2\n{FORMAT_CODES[args.format]}\n\n0\nq\n"
    subprocess.run(
        [args.executable], cwd=args.output_dir, input=commands, text=True, check=True
    )
    if not any(args.output_dir.iterdir()):
        parser.exit(1, "Multiwfn 未生成文件，请核对该版本的交互菜单\n")


if __name__ == "__main__":
    main()
