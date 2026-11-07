"""为 extxyz 增加整数 group 属性（依赖 ASE、NumPy），保留其他原子属性。

用法：python group_xyz.py model.xyz grouped.xyz --species Ge=0 Te=1
      python group_xyz.py model.xyz grouped.xyz --ranges=-1:64:0,64:127:1
--ranges 为 z 坐标范围，单位 Å，左闭右开；每个原子都必须匹配一个分组。
"""

import argparse
from pathlib import Path


def assign_groups(atoms, species=None, ranges=None):
    import numpy as np

    groups = np.full(len(atoms), -1, dtype=int)
    if species:
        mapping = dict(item.split("=", 1) for item in species)
        for i, symbol in enumerate(atoms.get_chemical_symbols()):
            if symbol not in mapping:
                raise ValueError(f"元素 {symbol} 没有对应的组")
            groups[i] = int(mapping[symbol])
    else:
        for specification in ranges.split(","):
            low, high, group = specification.split(":")
            low, high, group = float(low), float(high), int(group)
            if low >= high or group < 0:
                raise ValueError("范围上下界或组编号无效")
            mask = (atoms.positions[:, 2] >= low) & (atoms.positions[:, 2] < high)
            if (groups[mask] != -1).any():
                raise ValueError("分组范围重叠")
            groups[mask] = group
    if (groups < 0).any():
        raise ValueError("存在未分组原子或负数组编号")
    atoms.set_array("group", groups)
    return atoms


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--species", nargs="+", help="元素到组编号的映射，如 Ge=0 Te=1")
    mode.add_argument("--ranges", help="z_min:z_max:group，多个范围用逗号分隔")
    args = parser.parse_args()
    if args.output.exists():
        parser.error("输出文件已存在")
    from ase.io import read, write

    try:
        images = read(args.input, index=":")
        for atoms in images:
            assign_groups(atoms, args.species, args.ranges)
        write(args.output, images, format="extxyz")
    except (ValueError, OSError) as error:
        parser.exit(1, f"错误：{error}\n")


if __name__ == "__main__":
    main()
