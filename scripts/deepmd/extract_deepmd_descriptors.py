"""从 DeepMD 模型提取描述符与能量（依赖 deepmd-kit、ASE、NumPy）。

用法：python extract_deepmd_descriptors.py graph.pb ase_dataset.db Ge Te -a
-a 输出逐原子描述符及模型原子能；否则输出逐结构描述符与输入结构的参考能/eV·atom⁻¹。
结构描述符默认按原子求和（兼容原脚本），可用 --aggregation mean 改为均值。
输出 descriptors.npy、energies.npy；现有输出不覆盖，不修改输入数据库。
"""

import argparse
import os
import tempfile
from pathlib import Path


def extract(model, frames, type_map, atomic=False, aggregation="sum"):
    import numpy as np

    if not type_map or len(set(type_map)) != len(type_map):
        raise ValueError("type_map 必须非空且不能重复")
    if aggregation not in {"sum", "mean"}:
        raise ValueError("aggregation 只支持 sum 或 mean")
    descriptors, energies = [], []
    dimension = None
    for atoms in frames:
        if not len(atoms):
            raise ValueError("结构中没有原子")
        try:
            types = [type_map.index(s) for s in atoms.get_chemical_symbols()]
        except ValueError as error:
            raise ValueError("结构包含 type_map 未定义的元素") from error
        if atoms.pbc.any() and not atoms.pbc.all():
            raise ValueError("DeepMD 此入口只支持全周期或全非周期结构")
        coords = atoms.positions.reshape(1, -1)
        cell = atoms.cell.array.reshape(1, 9) if atoms.pbc.all() else None
        descriptor = np.asarray(model.eval_descriptor(coords, cell, types))
        if descriptor.ndim != 3 or descriptor.shape[:2] != (1, len(atoms)):
            raise ValueError("模型描述符应为 (1, natoms, ndim)")
        values = descriptor[0]
        if dimension is not None and dimension != values.shape[1]:
            raise ValueError("不同帧的描述符维度不一致")
        dimension = values.shape[1]
        if atomic:
            descriptors.append(values.astype(np.float32))
            energy = np.asarray(
                model.eval(coords, cell, types, atomic=True)[3]
            ).reshape(-1)
            if len(energy) != len(atoms):
                raise ValueError("模型原子能数目与原子数不符")
            energies.append(energy)
        else:
            descriptors.append(
                values.mean(axis=0) if aggregation == "mean" else values.sum(axis=0)
            )
            energies.append(atoms.get_potential_energy() / len(atoms))
    if not descriptors:
        raise ValueError("输入数据集为空")
    descriptor = np.concatenate(descriptors) if atomic else np.asarray(descriptors)
    energy = np.concatenate(energies) if atomic else np.asarray(energies)
    if (
        not descriptor.shape[1]
        or not np.isfinite(descriptor).all()
        or not np.isfinite(energy).all()
    ):
        raise ValueError("描述符或能量为空或含非有限数")
    return descriptor, energy


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("model", type=Path)
    parser.add_argument("dataset", type=Path)
    parser.add_argument("type_map", nargs="+")
    parser.add_argument("-a", "--atomic", action="store_true")
    parser.add_argument("--aggregation", choices=["sum", "mean"], default="sum")
    parser.add_argument("--output-dir", type=Path, default=Path("."))
    args = parser.parse_args()
    if not args.model.is_file() or not args.dataset.is_file():
        parser.error("模型或数据集不存在")
    outputs = [args.output_dir / name for name in ("descriptors.npy", "energies.npy")]
    if any(p.exists() or p.is_symlink() for p in outputs):
        parser.error("输出已存在")
    import numpy as np
    from ase.io import iread
    from deepmd.infer import DeepPot

    try:
        descriptor, energy = extract(
            DeepPot(str(args.model)),
            iread(args.dataset, index=":"),
            args.type_map,
            args.atomic,
            args.aggregation,
        )
        args.output_dir.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(
            dir=args.output_dir, prefix=".descriptors-"
        ) as folder:
            for output, data in zip(outputs, (descriptor, energy)):
                staged = Path(folder) / output.name
                np.save(staged, data)
            for output in outputs:
                os.link(Path(folder) / output.name, output)
    except (OSError, ValueError, RuntimeError) as error:
        parser.exit(1, f"错误：{error}\n")
    print(
        f"描述符 {descriptor.shape}；能量 {energy.shape}；输出目录：{args.output_dir}"
    )


if __name__ == "__main__":
    main()
