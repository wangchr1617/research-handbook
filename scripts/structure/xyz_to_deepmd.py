"""将带能量、力标签的 ExtXYZ 转为 DeepMD NumPy（依赖 dpdata）。

用法：python xyz_to_deepmd.py dataset.xyz [-o train] [--set-size 2000]
现有输出目录不会覆盖；set-size 是每个 set.* 的最大帧数。
"""

import argparse
import tempfile
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("-o", "--output", type=Path, default=Path("train"))
    parser.add_argument("--set-size", type=int, default=2000)
    args = parser.parse_args()
    if not args.input.is_file() or args.set_size <= 0:
        parser.error("输入必须存在，set-size 必须为正整数")
    if args.output.exists() or args.output.is_symlink():
        parser.error("输出目录已存在")
    import dpdata

    try:
        systems = dpdata.MultiSystems.from_file(str(args.input), fmt="quip/gap/xyz")
        count = sum(len(system) for system in systems)
        if not count:
            raise ValueError("输入没有结构")
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(
            dir=args.output.parent, prefix=".deepmd-"
        ) as folder:
            staged = Path(folder) / "train"
            systems.to_deepmd_npy(str(staged), set_size=args.set_size)
            staged.rename(args.output)
    except (OSError, ValueError, RuntimeError, KeyError) as error:
        parser.exit(1, f"错误：{error}\n")
    print(f"已转换 {count} 帧：{args.output}")


if __name__ == "__main__":
    main()
