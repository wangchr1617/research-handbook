"""将 ASE 结构、描述符和能量生成 Chemiscope 输入（依赖 ASE、chemiscope、NumPy）。

用法：python create_chemiscope_input.py -a 8 ase_dataset.db descriptors.npy energies.npy
-a 为原子局域环境截断半径/Å；省略时每个描述符对应一帧结构。
逐列标准化后做最多三维 PCA；常量列归零，小数据用零列补足三维。
"""

import argparse
import math
from pathlib import Path


def project(descriptors, energies, expected):
    """用 SVD 完成标准化 PCA，不依赖全局状态；返回固定三列坐标。"""
    import numpy as np

    descriptors = np.asarray(descriptors, dtype=float)
    energies = np.asarray(energies, dtype=float)
    if (
        descriptors.ndim != 2
        or descriptors.shape[0] != expected
        or not descriptors.shape[1]
        or expected <= 0
    ):
        raise ValueError("描述符须为非空二维数组，行数与结构/原子数一致")
    if energies.shape != (expected,):
        raise ValueError("能量须为一维数组，长度与描述符行数一致")
    if not np.isfinite(descriptors).all() or not np.isfinite(energies).all():
        raise ValueError("描述符或能量含非有限数")
    std = descriptors.std(axis=0)
    normalized = (descriptors - descriptors.mean(axis=0)) / np.where(std > 0, std, 1)
    u, singular, _ = np.linalg.svd(normalized, full_matrices=False)
    dimensions = min(3, len(singular))
    projected = np.zeros((expected, 3))
    projected[:, :dimensions] = u[:, :dimensions] * singular[:dimensions]
    return projected


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("dataset", type=Path)
    parser.add_argument("descriptors", type=Path)
    parser.add_argument("energies", type=Path)
    parser.add_argument("-a", "--atomic", type=float, help="局域环境截断半径/Å")
    parser.add_argument("-o", "--output", type=Path, default=Path("chemiscope.json.gz"))
    args = parser.parse_args()
    if args.atomic is not None and (not math.isfinite(args.atomic) or args.atomic <= 0):
        parser.error("截断半径必须为有限正数")
    if args.output.exists() or args.output.is_symlink():
        parser.error("输出已存在")
    if args.output.suffix != ".json" and not args.output.name.endswith(".json.gz"):
        parser.error("输出需以 .json 或 .json.gz 结尾")
    import numpy as np
    from ase.io import read

    try:
        frames = read(args.dataset, index=":")
        expected = sum(map(len, frames)) if args.atomic is not None else len(frames)
        energies = np.load(args.energies, allow_pickle=False)
        projected = project(
            np.load(args.descriptors, allow_pickle=False), energies, expected
        )
        import chemiscope as cs

        target = "atom" if args.atomic is not None else "structure"
        properties = {
            "PCA": {
                "target": target,
                "values": projected,
                "description": "标准化描述符的 PCA 坐标",
            },
            "energies": {
                "target": target,
                "values": energies,
                "units": "eV" if target == "atom" else "eV/atom",
                "description": "模型原子能" if target == "atom" else "每原子参考能",
            },
        }
        kwargs = (
            {"environments": cs.all_atomic_environments(frames, args.atomic)}
            if target == "atom"
            else {}
        )
        cs.write_input(
            path=str(args.output), frames=frames, properties=properties, **kwargs
        )
    except (OSError, ValueError, RuntimeError) as error:
        parser.exit(1, f"错误：{error}\n")
    print(f"已生成：{args.output}")


if __name__ == "__main__":
    main()
