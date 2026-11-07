"""三端点分段线性插值，生成双原子拉伸等扫描结构（依赖 ASE）。

用法：python generate_dimer_scan.py ini mid fin --output-dir dimer --first-images 9 --second-images 24
各 images 参数为区间内部插入的结构数；中间端点只保存一次。晶胞和原子顺序必须一致。
使用笛卡尔直线插值，不自动选择周期最短路径，也不执行结构优化。
"""

import argparse
from pathlib import Path


def interpolate(start, end, images):
    import numpy as np

    if start.get_chemical_symbols() != end.get_chemical_symbols() or not np.allclose(
        start.cell, end.cell
    ):
        raise ValueError("端点元素顺序或晶胞不一致")
    result = []
    for weight in np.linspace(0, 1, images + 2):
        atoms = start.copy()
        atoms.set_positions(
            (1 - weight) * start.positions + weight * end.positions,
            apply_constraint=False,
        )
        result.append(atoms)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("initial", "middle", "final"):
        parser.add_argument(name, type=Path)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--first-images", type=int, default=9)
    parser.add_argument("--second-images", type=int, default=24)
    parser.add_argument(
        "--copy-input",
        nargs="*",
        type=Path,
        default=[],
        help="需复制至每个任务的 INCAR、POTCAR 等文件",
    )
    args = parser.parse_args()
    if min(args.first_images, args.second_images) < 0 or args.output_dir.exists():
        parser.error("插入数不能为负，输出目录必须不存在")
    if any(not p.is_file() for p in args.copy_input):
        parser.error("待复制输入不存在")
    import shutil

    from ase.io import read, write

    initial, middle, final = [
        read(p, format="vasp") for p in (args.initial, args.middle, args.final)
    ]
    frames = (
        interpolate(initial, middle, args.first_images)
        + interpolate(middle, final, args.second_images)[1:]
    )
    for index, atoms in enumerate(frames):
        directory = args.output_dir / f"{index:03d}"
        directory.mkdir(parents=True)
        write(directory / "POSCAR", atoms, format="vasp", direct=True)
        for source in args.copy_input:
            shutil.copy2(source, directory / source.name)
    print(f"已生成 {len(frames)} 个结构")


if __name__ == "__main__":
    main()
