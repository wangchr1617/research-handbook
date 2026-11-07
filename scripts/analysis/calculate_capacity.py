"""按明确的电子计量与结构质量计算比容量（依赖 ASE）。

用法：python calculate_capacity.py structures Li 1 -o capacity.csv
位置参数：结构目录、阳离子名称（可多个）、每个输入晶胞转移的阳离子数。
电荷默认 Li/Na/K=+1、Mg/Ca=+2、Al=+3；其他阳离子须用 --charge 元素=电荷 指定。
输出 mAh/g，以输入结构质量归一；该计算不预测可达插入量或电压。
"""

import argparse
import csv
import math
from pathlib import Path

FARADAY = 96485.33212  # C/mol
DEFAULT_CHARGES = {"Li": 1, "Na": 1, "K": 1, "Mg": 2, "Ca": 2, "Al": 3}


def calculate_capacity(
    path, cations, num_cations, charges=None, output=Path("capacity.csv")
):
    from ase.io import read

    if not math.isfinite(num_cations) or num_cations < 0:
        raise ValueError("阳离子数量必须为有限非负数")
    if len(cations) != len(set(cations)) or not cations:
        raise ValueError("阳离子名称须非空且不能重复")
    mapping = {**DEFAULT_CHARGES, **(charges or {})}
    for name in cations:
        charge = mapping.get(name)
        if charge is None or not math.isfinite(charge) or charge <= 0:
            raise ValueError(f"请显式指定 {name} 的正电荷：--charge {name}=电荷")
    output = Path(output)
    if output.exists() or output.is_symlink():
        raise FileExistsError(f"输出已存在：{output}")
    path = Path(path)
    if not path.is_dir():
        raise ValueError("结构目录不存在")
    sources = sorted(
        p for p in path.iterdir() if p.is_file() and p.resolve() != output.resolve()
    )
    if not sources:
        raise ValueError("目录中没有结构文件")
    rows = []
    for source in sources:
        atoms = read(source)
        mass = float(atoms.get_masses().sum())  # g/mol of input cells
        if not math.isfinite(mass) or mass <= 0:
            raise ValueError(f"{source} 的质量无效")
        row = {"source": source.name, "formula": atoms.get_chemical_formula()}
        row.update(
            {
                name: num_cations * mapping[name] * FARADAY / (3.6 * mass)
                for name in cations
            }
        )
        rows.append(row)
    with output.open("x", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=["source", "formula", *cations])
        writer.writeheader()
        writer.writerows(rows)
    return rows


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    parser.add_argument("cations", nargs="+")
    parser.add_argument("num_cations", type=float)
    parser.add_argument("--charge", action="append", default=[], metavar="ELEMENT=Z")
    parser.add_argument("-o", "--output", type=Path, default=Path("capacity.csv"))
    args = parser.parse_args()
    try:
        charges = {}
        for item in args.charge:
            name, value = item.split("=", 1)
            if name in charges or name not in args.cations:
                raise ValueError("电荷参数重复或元素不在阳离子列表中")
            charges[name] = float(value)
        rows = calculate_capacity(
            args.directory, args.cations, args.num_cations, charges, args.output
        )
    except (OSError, ValueError, RuntimeError, IndexError) as error:
        parser.exit(1, f"错误：{error}\n")
    print(f"已计算 {len(rows)} 个结构，比容量单位 mAh/g：{args.output}")


if __name__ == "__main__":
    main()
