"""收集子目录的结构文件。用法：python collect_structures.py ROOT --output collected。

--filename 默认 CONTCAR；复制为“子目录名.vasp”，不会移动或改写源文件。
"""

import argparse
import shutil
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--filename", default="CONTCAR", help="要收集的文件名")
    args = parser.parse_args()
    sources = sorted(args.root.glob(f"*/{args.filename}"))
    if not sources:
        parser.error("未找到结构文件")
    args.output.mkdir(parents=True, exist_ok=True)
    # 在复制前检查所有目标。
    targets = [args.output / f"{p.parent.name}.vasp" for p in sources]
    if any(p.exists() for p in targets):
        parser.error("输出文件已经存在")
    for source, target in zip(sources, targets):
        shutil.copy2(source, target)
    print(f"已收集 {len(sources)} 个结构")


if __name__ == "__main__":
    main()
