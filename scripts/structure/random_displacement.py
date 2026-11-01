"""对选定元素施加独立笛卡尔随机扰动（依赖 ASE、NumPy）。

用法：python random_displacement.py POSCAR --elements Ge --count 100 --seed 42 --output-dir displaced
位移每个分量均匀分布于 [-a,a]，a 在 min/max-displacement 之间随机选取，单位 Å；不扰动晶胞。
"""

import argparse
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("--elements", nargs="+", required=True)
    parser.add_argument("--count", type=int, default=500, help="生成结构数")
    parser.add_argument(
        "--min-displacement", type=float, default=0.01, help="幅度下限/Å"
    )
    parser.add_argument(
        "--max-displacement", type=float, default=0.05, help="幅度上限/Å"
    )
    parser.add_argument("--seed", type=int, help="随机种子，用于复现")
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    if (
        args.count <= 0
        or not 0 <= args.min_displacement <= args.max_displacement
        or args.output_dir.exists()
    ):
        parser.error("数量或位移范围无效，或输出目录已存在")
    import numpy as np
    from ase.io import read, write

    atoms = read(args.input)
    symbols = np.array(atoms.get_chemical_symbols())
    if not set(args.elements).issubset(symbols):
        parser.error("指定元素不在输入结构中")
    mask = np.isin(symbols, args.elements)
    random = np.random.default_rng(args.seed)
    args.output_dir.mkdir(parents=True)
    for index in range(args.count):
        amplitude = random.uniform(args.min_displacement, args.max_displacement)
        image = atoms.copy()
        image.positions[mask] += random.uniform(
            -amplitude, amplitude, size=(mask.sum(), 3)
        )
        write(
            args.output_dir / f"displaced_{index:04d}.vasp",
            image,
            format="vasp",
            direct=True,
        )


if __name__ == "__main__":
    main()
