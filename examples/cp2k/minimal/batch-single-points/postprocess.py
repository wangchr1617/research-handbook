"""用法：python3 postprocess.py；核对两组单点计算，导出 eV/Å 单位的 ExtXYZ 标签。"""

import json
import re
from pathlib import Path

import numpy as np
from ase.calculators.singlepoint import SinglePointCalculator
from ase.io import read, write
from ase.units import Bohr, Hartree
from run import CASES

MAX_NET_FORCE_EV_A = 0.005  # 孤立水分子示例的净力检查阈值，单位 eV/Å；按精度目标调整。


def main():
    frames, records = [], []
    for name in CASES:
        directory = Path("runs") / name
        text = (directory / "cp2k.out").read_text(errors="replace")
        if (
            "PROGRAM ENDED AT" not in text
            or "SCF run converged" not in text
            or "SCF run NOT converged" in text
        ):
            raise SystemExit(f"{name} 未正常结束或 SCF 未收敛")
        energies = re.findall(
            r"ENERGY\| Total FORCE_EVAL.*?energy.*?\s+([-+0-9.Ee]+)\s*$",
            text,
            re.MULTILINE,
        )
        if len(energies) != 1:
            raise SystemExit(f"{name} 应是单点计算，能量条目数量不符")
        atoms = read(directory / "structure.xyz")
        rows = re.findall(
            r"^\s*FORCES\|\s+\d+\s+([-+0-9.Ee]+)\s+([-+0-9.Ee]+)\s+([-+0-9.Ee]+)\s+[-+0-9.Ee]+\s*$",
            text,
            re.MULTILINE,
        )
        forces = np.array(rows, dtype=float) * Hartree / Bohr
        energy = float(energies[0]) * Hartree
        if (
            forces.shape != (len(atoms), 3)
            or not np.isfinite(forces).all()
            or not np.isfinite(energy)
        ):
            raise SystemExit(f"{name} 的力标签不完整")
        if np.linalg.norm(forces.sum(axis=0)) > MAX_NET_FORCE_EV_A:
            raise SystemExit(f"{name} 的净力偏大，请检查网格和边界条件")
        atoms.pbc = False
        atoms.calc = SinglePointCalculator(atoms, energy=energy, forces=forces)
        atoms.info["config_type"] = name
        frames.append(atoms)
        records.append(
            {
                "case": name,
                "energy_eV": energy,
                "max_force_eV_A": float(np.linalg.norm(forces, axis=1).max()),
                "net_force_eV_A": float(np.linalg.norm(forces.sum(axis=0))),
            }
        )
    write("labeled-structures.xyz", frames, format="extxyz")
    restored = read("labeled-structures.xyz", index=":", format="extxyz")
    for before, after in zip(frames, restored):
        if not np.isclose(
            before.get_potential_energy(), after.get_potential_energy()
        ) or not np.allclose(before.get_forces(), after.get_forces(), atol=1e-7):
            raise SystemExit("ExtXYZ 回读的能量或力与原标签不符")
    Path("batch-results.json").write_text(json.dumps(records, indent=2) + "\n")
    print(json.dumps(records, indent=2))


if __name__ == "__main__":
    main()
