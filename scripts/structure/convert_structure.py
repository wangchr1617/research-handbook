"""结构/轨迹格式转换（依赖 ASE）。

用法：python convert_structure.py POSCAR model.xyz --repeat 2 2 2
      python convert_structure.py cp2k-pos-1.xyz last.cif --index -1 --cell-from POSCAR
      python convert_structure.py XDATCAR trajectory.xyz --unwrap
--cell-from 指定晶胞来源；--unwrap 仅适用于固定晶胞轨迹，保持首帧位置不变。
"""

import argparse
from pathlib import Path


def convert(args):
    import numpy as np
    from ase.io import read, write

    frames = read(args.input, index=args.index, format=args.input_format)
    if not isinstance(frames, list):
        frames = [frames]
    if not frames:
        raise ValueError("未选中任何结构")
    reference = read(args.cell_from) if args.cell_from else None
    previous = accumulated = None
    initial_cell = frames[0].cell.copy()
    for atoms in frames:
        if reference is not None:
            if (
                len(atoms) != len(reference)
                or atoms.get_chemical_symbols() != reference.get_chemical_symbols()
            ):
                raise ValueError("轨迹与参考晶胞结构的原子数或元素顺序不一致")
            atoms.set_cell(reference.cell)
            atoms.pbc = reference.pbc
        if args.cell:
            atoms.set_cell(np.array(args.cell).reshape(3, 3))
            atoms.pbc = True
        if args.unwrap:
            if atoms.cell.rank != 3 or not atoms.pbc.any():
                raise ValueError("--unwrap 需要带周期晶胞的轨迹")
            if not np.allclose(atoms.cell, initial_cell):
                raise ValueError("--unwrap 不支持变胞轨迹")
            current = atoms.get_scaled_positions(wrap=False)
            if previous is None:
                accumulated = current.copy()
            else:
                delta = current - previous
                delta[:, atoms.pbc] -= np.round(delta[:, atoms.pbc])
                accumulated += delta
            previous = current.copy()
            atoms.set_scaled_positions(accumulated)
    result = []
    for atoms in frames:
        atoms = atoms.repeat(args.repeat)
        if args.sort_elements:
            from ase.build import sort

            atoms = sort(atoms)
        if args.sort_axis:
            axis = "xyz".index(args.sort_axis)
            indices = np.argsort(atoms.positions[:, axis], kind="stable")
            atoms = atoms[indices[::-1] if args.descending else indices]
        result.append(atoms)
    write(args.output, result, format=args.output_format)
    return len(result)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--input-format", help="如 vasp、vasp-xdatcar、xyz")
    parser.add_argument("--output-format", help="如 extxyz、cif、vasp、vasp-xdatcar")
    parser.add_argument("--index", default=":", help="ASE 帧索引，如 -1、0:100:10")
    cell = parser.add_mutually_exclusive_group()
    cell.add_argument("--cell-from", type=Path)
    cell.add_argument(
        "--cell", nargs=9, type=float, help="行优先排列的 3×3 晶胞，单位 Å"
    )
    parser.add_argument(
        "--repeat", nargs=3, type=int, default=[1, 1, 1], help="各方向扩胞倍数"
    )
    parser.add_argument("--sort-axis", choices=["x", "y", "z"])
    parser.add_argument("--descending", action="store_true")
    parser.add_argument(
        "--sort-elements", action="store_true", help="按元素排序，如 CIF→VASP"
    )
    parser.add_argument("--unwrap", action="store_true")
    args = parser.parse_args()
    if any(n <= 0 for n in args.repeat):
        parser.error("扩胞倍数必须为正整数")
    if args.output.exists():
        parser.error("输出文件已存在")
    if args.unwrap and (args.cell or args.cell_from):
        parser.error(
            "--unwrap 请直接使用带有晶胞的轨迹，不与 --cell / --cell-from 联用"
        )
    try:
        print(f"已转换 {convert(args)} 帧")
    except (ValueError, OSError, RuntimeError) as error:
        parser.exit(1, f"错误：{error}\n")


if __name__ == "__main__":
    main()
