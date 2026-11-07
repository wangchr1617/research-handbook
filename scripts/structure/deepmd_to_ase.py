"""将 DeepMD NumPy 数据转为 ASE 数据库（依赖 dpdata、ASE、NumPy）。

用法：python deepmd_to_ase.py train Ge Te -o ase_dataset.db
元素顺序须与 type.raw 一致；virial/eV 转为 ASE stress/eV·Å⁻³。
读取所有 set.* 分片；缺标签、形状不一致或非有限值时终止，不发布部分结果。
"""

import argparse
import os
import tempfile
from pathlib import Path


def validate_data(data):
    import numpy as np

    types = np.asarray(data["atom_types"])
    names = data["atom_names"]
    if types.ndim != 1 or not len(types) or not np.issubdtype(types.dtype, np.integer):
        raise ValueError("atom_types 必须为非空整数向量")
    if np.any(types < 0) or np.any(types >= len(names)):
        raise ValueError("元素索引超出 type_map")
    frames, atoms = len(data["coords"]), len(types)
    if not frames:
        raise ValueError("数据集中没有结构")
    shapes = {
        "coords": (frames, atoms, 3),
        "cells": (frames, 3, 3),
        "energies": (frames,),
        "forces": (frames, atoms, 3),
    }
    if "virials" in data:
        shapes["virials"] = (frames, 3, 3)
    for key, shape in shapes.items():
        if key not in data:
            raise ValueError(f"缺少训练标签：{key}")
        values = np.asarray(data[key])
        if values.shape != shape or not np.isfinite(values).all():
            raise ValueError(f"{key} 应为 {shape} 且全部有限")
    if not data.get("nopbc", False) and np.any(
        np.abs(np.linalg.det(data["cells"])) < 1e-12
    ):
        raise ValueError("周期晶胞奇异，无法定义应力")


def iter_systems(root, type_map=None):
    """稳定排序读取系统；元素名称须由 type_map.raw 或调用者提供。"""
    from dpdata import LabeledSystem

    root = Path(root)
    if not root.is_dir():
        raise ValueError(f"输入目录不存在：{root}")
    files = sorted(root.rglob("type.raw"))
    if not files:
        raise ValueError("未找到 DeepMD type.raw 文件")
    for file in files:
        if not type_map and not file.with_name("type_map.raw").is_file():
            raise ValueError(f"{file.parent} 缺少 type_map.raw，请显式提供元素顺序")
        data = LabeledSystem(str(file.parent), fmt="deepmd/npy", type_map=type_map).data
        validate_data(data)
        yield file.parent, data


def to_ase(data):
    from ase import Atoms
    from ase.calculators.singlepoint import SinglePointCalculator
    from ase.stress import full_3x3_to_voigt_6_stress

    validate_data(data)
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
            if atoms.get_volume() <= 0:
                raise ValueError("virial 转应力需要非零晶胞体积")
            results["stress"] = full_3x3_to_voigt_6_stress(
                -data["virials"][index] / atoms.get_volume()
            )
        atoms.calc = SinglePointCalculator(atoms, **results)
        structures.append(atoms)
    return structures


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", type=Path)
    parser.add_argument("type_map", nargs="*", help="元素顺序；省略则读取 type_map.raw")
    parser.add_argument("-o", "--output", type=Path, default=Path("ase_dataset.db"))
    args = parser.parse_args()
    if args.output.exists() or args.output.is_symlink():
        parser.error("输出数据库已存在")
    from ase.db import connect

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(
        dir=args.output.parent, prefix=".deepmd-"
    ) as folder:
        temporary = Path(folder) / "dataset.db"
        try:
            count = 0
            with connect(temporary) as database:
                for source, data in iter_systems(args.root, args.type_map or None):
                    for atoms in to_ase(data):
                        database.write(atoms, source=str(source))
                        count += 1
            os.link(temporary, args.output)
        except (OSError, ValueError, RuntimeError, KeyError) as error:
            parser.exit(1, f"错误：{error}\n")
    print(f"已写入 {count} 帧：{args.output}")


if __name__ == "__main__":
    main()
