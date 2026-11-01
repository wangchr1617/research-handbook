"""用法：python3 postprocess.py；检查孤立体系的单点能、完整受力和净力。"""

import json
import re
from pathlib import Path

import numpy as np
from ase.io import read
from ase.units import Bohr, Hartree

MAX_NET_FORCE_EV_A = 0.005  # 孤立体系的数值净力检查阈值，eV/Å；不代表结构已优化。


def main():
    text = Path("cp2k.out").read_text(errors="replace")
    energies = re.findall(
        r"ENERGY\| Total FORCE_EVAL.*?energy.*?\s+([-+0-9.Ee]+)\s*$", text, re.MULTILINE
    )
    rows = re.findall(
        r"^\s*FORCES\|\s+\d+\s+([-+0-9.Ee]+)\s+([-+0-9.Ee]+)\s+([-+0-9.Ee]+)\s+[-+0-9.Ee]+\s*$",
        text,
        re.MULTILINE,
    )
    atoms = read("structure.xyz")
    forces = np.array(rows, dtype=float) * Hartree / Bohr
    if (
        "PROGRAM ENDED AT" not in text
        or "SCF run converged" not in text
        or "SCF run NOT converged" in text
        or len(energies) != 1
    ):
        raise SystemExit("单点未正常结束或 SCF 未收敛")
    if forces.shape != (len(atoms), 3) or not np.isfinite(forces).all():
        raise SystemExit("受力输出不完整或含非有限值")
    energy = float(energies[0])
    if not np.isfinite(energy):
        raise SystemExit("能量不是有限值")
    net_force = float(np.linalg.norm(forces.sum(axis=0)))
    result = {
        "energy_Hartree": energy,
        "energy_eV": energy * Hartree,
        "forces_eV_A": forces.tolist(),
        "max_force_eV_A": float(np.linalg.norm(forces, axis=1).max()),
        "net_force_eV_A": net_force,
        "scf_converged": True,
        "completed": True,
    }
    Path("results.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))
    if net_force > MAX_NET_FORCE_EV_A:
        raise SystemExit("孤立体系净力偏大，请检查积分网格和边界条件")


if __name__ == "__main__":
    main()
