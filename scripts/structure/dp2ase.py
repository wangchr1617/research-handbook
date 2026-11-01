"""将 DeepMD NumPy 数据集转换为 ASE 数据库（依赖 dpdata、ASE）。

用法：python dp2ase.py train Ge Te -o ase_dataset.db
元素顺序须与 type.raw 一致；virial/eV 转为 ASE stress/eV·Å⁻³。
"""

import argparse
import os
import tempfile
from pathlib import Path


def to_ase(data):
    from ase import Atoms
    from ase.calculators.singlepoint import SinglePointCalculator
    from ase.stress import full_3x3_to_voigt_6_stress

    species = [data["atom_names"][index] for index in data["atom_types"]]
    structures = []
    for index in range(len(data["coords"])):
        atoms = Atoms(
            symbols=species,
            positions=data["coords"][index],
            cell=data["cells"][index],
            pbc=not data.get("nopbc", False),
        )
        results = {
            "energy": float(data["energies"][index]),
            "forces": data["forces"][index],
        }
        if "virials" in data:
            results["stress"] = full_3x3_to_voigt_6_stress(
                -data["virials"][index] / atoms.get_volume()
            )
        atoms.calc = SinglePointCalculator(atoms, **results)
        structures.append(atoms)
    return structures


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", type=Path)
    parser.add_argument("type_map", nargs="+", help="元素名称，顺序与类型索引一致")
    parser.add_argument("-o", "--output", type=Path, default=Path("ase_dataset.db"))
    args = parser.parse_args()
    if args.output.exists():
        parser.error("输出数据库已存在")
    from ase.io import write
    from dpdata import LabeledSystem

    files = sorted(args.root.rglob("type.raw"))
    if not files:
        parser.error("未找到 DeepMD type.raw 文件")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        dir=args.output.parent, suffix=".db", delete=False
    ) as stream:
        temporary = Path(stream.name)
    # SQLite 不能读取空文件作为有效数据库；使用该预留名称重新创建。
    temporary.unlink()
    try:
        images = []
        for file in files:
            data = LabeledSystem(
                str(file.parent), fmt="deepmd/npy", type_map=args.type_map
            ).data
            images.extend(to_ase(data))
        if not images:
            parser.error("数据集中没有结构")
        write(temporary, images, format="db")
        os.replace(temporary, args.output)
    finally:
        temporary.unlink(missing_ok=True)
        temporary.with_name(temporary.name + ".lock").unlink(missing_ok=True)
    print(f"已写入 {len(images)} 帧：{args.output}")


if __name__ == "__main__":
    main()
