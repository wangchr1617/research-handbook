"""将全部 DeepMD NumPy 分片导出为扩展 XYZ 或旧版 NEP train.in。

用法：python deepmd_to_xyz.py train/Ge12Te12 -o train.xyz
      python deepmd_to_xyz.py train --format nep --nep-version 3 -o train.in
默认输出 XYZ/DEEP2XYZ.xyz；缺 type_map.raw 时用 --type-map Ge Te 指定元素顺序。
能量、力、virial 单位分别为 eV、eV/Å、eV；保留 nopbc，缺 virial 时省略。
"""

import argparse
import os
import tempfile
from pathlib import Path

from deepmd_to_ase import iter_systems, to_ase


def write_nep(stream, frames, version):
    """保留旧版 NEP 1/2/3 的文件布局；类型 2 的索引需全局一致。"""
    import numpy as np

    names = list(
        dict.fromkeys(s for atoms in frames for s in atoms.get_chemical_symbols())
    )
    stream.write(f"{len(frames)}\n")
    for atoms in frames:
        stream.write(f"{len(atoms)} {int('virial' in atoms.info)}\n")
    for atoms in frames:
        row = [atoms.get_potential_energy()]
        if "virial" in atoms.info:
            row.extend(np.asarray(atoms.info["virial"]).reshape(9)[[0, 4, 8, 1, 5, 2]])
        stream.write(" ".join(map(str, row)) + "\n")
        stream.write(" ".join(map(str, atoms.cell.array.reshape(9))) + "\n")
        for atom, force in zip(atoms, atoms.get_forces()):
            symbol = (
                atom.number
                if version == 1
                else names.index(atom.symbol)
                if version == 2
                else atom.symbol
            )
            stream.write(
                f"{symbol} " + " ".join(map(str, [*atom.position, *force])) + "\n"
            )
    return names


def convert(root, output, type_map=None, fmt="extxyz", nep_version=3):
    import numpy as np
    from ase.io import write

    if output.exists() or output.is_symlink():
        raise FileExistsError(f"输出已存在：{output}")
    if fmt not in {"extxyz", "nep"} or nep_version not in {1, 2, 3}:
        raise ValueError("输出格式或 NEP 版本无效")
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(mode="w", dir=output.parent) as stream:
        count = 0
        legacy = []
        for source, data in iter_systems(root, type_map):
            for index, atoms in enumerate(to_ase(data)):
                atoms.info["config_type"] = source.name
                if "virials" in data:
                    # ExtXYZ 明确保留能量量纲的 virial，不同时输出重复 stress 标签。
                    atoms.info["virial"] = np.asarray(data["virials"][index])
                    atoms.calc.results.pop("stress", None)
                if fmt == "extxyz":
                    write(stream, atoms, format="extxyz")
                else:
                    if not atoms.pbc.all():
                        raise ValueError(
                            "旧版 NEP 格式没有 nopbc 标志；非周期体系请用 extxyz"
                        )
                    legacy.append(atoms)
                count += 1
        if fmt == "nep":
            names = write_nep(stream, legacy, nep_version)
            print("NEP 元素索引顺序：" + " ".join(names))
        stream.flush()
        os.link(stream.name, output)
    return count


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", type=Path)
    parser.add_argument("--type-map", nargs="+")
    parser.add_argument("-o", "--output", type=Path, default=Path("XYZ/DEEP2XYZ.xyz"))
    parser.add_argument("--format", choices=["extxyz", "nep"], default="extxyz")
    parser.add_argument("--nep-version", type=int, choices=[1, 2, 3], default=3)
    args = parser.parse_args()
    try:
        count = convert(
            args.root, args.output, args.type_map, args.format, args.nep_version
        )
    except (OSError, ValueError, RuntimeError, KeyError) as error:
        parser.exit(1, f"错误：{error}\n")
    print(f"已写入 {count} 帧：{args.output}")


if __name__ == "__main__":
    main()
