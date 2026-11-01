"""将 VASP 结果统一导出为训练用 extxyz（依赖 ASE、NumPy）。

用法：python vasp2xyz.py calculations -o train.xyz --frames all --converged
默认每个计算取最后一帧，优先 vasprun.xml，失败时读取 OUTCAR。
能量默认 TOTEN 自由能/eV；--energy zero 取 ASE 的零温外推能量。
原 Shell 版本作者：yanzhowang@gmail.com；修改者：Yuwen Zhang、Shunda Chen。
"""

import argparse
import os
import re
import tempfile
from pathlib import Path
from xml.etree.ElementTree import ParseError as XMLParseError


def convergence_mask(directory, count, nelm=None):
    """按 OSZICAR 的电子步数筛选，不将离子优化结束与电子收敛混为一谈。"""
    oszicar = directory / "OSZICAR"
    if not oszicar.is_file():
        raise ValueError(f"{directory} 缺少 OSZICAR，无法筛选收敛帧")
    if nelm is None:
        outcar = directory / "OUTCAR"
        text = outcar.read_text(errors="replace") if outcar.exists() else ""
        match = re.search(r"\bNELM\s*=\s*(\d+)", text)
        if not match:
            raise ValueError("未找到 NELM；请通过 --nelm 指定电子步上限")
        nelm = int(match[1])
    mask, step = [], None
    for line in oszicar.read_text(errors="replace").splitlines():
        match = re.match(r"\s*(?:DAV|RMM|CG|DMP|RMM-DIIS):\s*(\d+)", line)
        if match:
            step = int(match[1])
        if "E0=" in line or "F=" in line:
            if step is None:
                raise ValueError(f"{oszicar} 缺少对应电子迭代记录")
            mask.append(step < nelm)
            step = None
    if len(mask) != count:
        raise ValueError(
            f"{directory} 的 OSZICAR({len(mask)}) 与结构帧({count})数量不一致"
        )
    return mask


def reject_ml_outputs(directory):
    """MLFF 轨迹可混有预测帧，不能当作纯 DFT 标签直接导出。"""
    for name in ("INCAR", "OUTCAR"):
        path = directory / name
        if not path.is_file():
            continue
        with path.open(errors="replace") as stream:
            text = stream.read(200000)
        for line in text.splitlines():
            active = re.split(r"[#!]", line, maxsplit=1)[0]
            if (
                re.search(r"\bML_LMLFF\s*=\s*\.?(?:TRUE|T)\.?(?:\s|;|$)", active, re.I)
                or "free  energy ML TOTEN" in active
            ):
                raise ValueError(
                    f"{directory} 包含 MLFF 计算，不能直接当作纯 DFT 标签；请使用独立 DFT 标注目录"
                )


def training_frame(
    atoms, label, energy_mode="free", include_virial=True, energy_shift=0.0
):
    import numpy as np
    from ase.calculators.singlepoint import SinglePointCalculator

    result = atoms.copy()
    energy = atoms.get_potential_energy(force_consistent=energy_mode == "free")
    forces = atoms.get_forces(apply_constraint=False)
    if include_virial:
        # ASE 应力为 eV/Å³，NEP virial = -应力 × 体积，单位 eV。
        result.info["virial"] = -atoms.get_stress(voigt=False) * atoms.get_volume()
    result.info["config_type"] = label
    result.info["Weight"] = 1.0
    result.calc = SinglePointCalculator(
        result, energy=energy - len(atoms) * energy_shift, forces=np.asarray(forces)
    )
    return result


def convert(
    root,
    output,
    frames="last",
    converged=False,
    nelm=None,
    label=None,
    energy_mode="free",
    include_virial=True,
    energy_shift=0.0,
):
    from ase.io import ParseError, read, write

    directories = {
        p.parent for name in ("OUTCAR", "vasprun.xml") for p in root.rglob(name)
    }
    if not directories:
        raise ValueError("没有找到 OUTCAR 或 vasprun.xml")
    for directory in directories:
        reject_ml_outputs(directory)
    if output.exists():
        raise FileExistsError(f"输出文件已存在：{output}")
    output.parent.mkdir(parents=True, exist_ok=True)
    written = 0
    # 先写临时文件，任何解析失败都不留下貌似完整的训练集。
    with tempfile.NamedTemporaryFile(
        dir=output.parent, suffix=".xyz", delete=False
    ) as stream:
        temporary = Path(stream.name)
    try:
        for directory in sorted(directories):
            xml = directory / "vasprun.xml"
            if xml.exists():
                try:
                    images = read(xml, index=":", format="vasp-xml")
                except (
                    ValueError,
                    OSError,
                    RuntimeError,
                    IndexError,
                    XMLParseError,
                    ParseError,
                ):
                    images = read(directory / "OUTCAR", index=":", format="vasp-out")
            else:
                images = read(directory / "OUTCAR", index=":", format="vasp-out")
            mask = (
                convergence_mask(directory, len(images), nelm)
                if converged
                else [True] * len(images)
            )
            selected = [atoms for atoms, valid in zip(images, mask) if valid]
            if frames == "last":
                selected = selected[-1:]
            for atoms in selected:
                image = training_frame(
                    atoms,
                    label or directory.name,
                    energy_mode,
                    include_virial,
                    energy_shift,
                )
                write(temporary, image, format="extxyz", append=True)
                written += 1
        if not written:
            raise ValueError("没有满足条件的帧")
        os.replace(temporary, output)
    finally:
        temporary.unlink(missing_ok=True)
    return written


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", type=Path, nargs="?", default=Path("."))
    parser.add_argument("-o", "--output", type=Path, default=Path("NEP-dataset.xyz"))
    parser.add_argument("--frames", choices=["all", "last"], default="last")
    parser.add_argument(
        "--converged", action="store_true", help="只保留电子迭代步数小于 NELM 的帧"
    )
    parser.add_argument("--nelm", type=int, help="电子步上限；默认从各 OUTCAR 读取")
    parser.add_argument("--label", help="配置类型标签；默认使用计算目录名")
    parser.add_argument("--energy", choices=["free", "zero"], default="free")
    parser.add_argument(
        "--energy-shift", type=float, default=0.0, help="每原子能量扣除值，单位 eV/atom"
    )
    parser.add_argument(
        "--no-virial", action="store_true", help="无应力数据时显式不导出 virial"
    )
    args = parser.parse_args()
    if args.nelm is not None and args.nelm <= 0:
        parser.error("NELM 必须为正整数")
    try:
        n = convert(
            args.root,
            args.output,
            args.frames,
            args.converged,
            args.nelm,
            args.label,
            args.energy,
            not args.no_virial,
            args.energy_shift,
        )
    except (OSError, ValueError, RuntimeError, IndexError) as error:
        parser.exit(1, f"错误：{error}\n")
    print(f"已写入 {n} 帧：{args.output}")


if __name__ == "__main__":
    main()
