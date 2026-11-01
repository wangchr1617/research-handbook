"""用法：python3 postprocess.py；检查冻结的 O、H1 和自由 H2 的全过程坐标。"""

import json
import re
import subprocess
import sys
from pathlib import Path

import numpy as np
from ase.io import read
from ase.units import Bohr, Hartree


def main():
    text = Path("cp2k.out").read_text(errors="replace")
    if (
        "PROGRAM ENDED AT" not in text
        or "GEOMETRY OPTIMIZATION COMPLETED" not in text
        or "SCF run NOT converged" in text
    ):
        raise SystemExit("计算或优化未收敛")
    initial = read("structure.xyz")
    frames = read("selective-pos-1.xyz", index=":")
    positions = np.array([initial.positions] + [a.positions for a in frames])
    delta = positions - positions[0]
    drift = float(np.max(np.abs(delta[:, :2, :])))
    movement = float(np.linalg.norm(delta[-1, 2]))
    if drift > 1e-6 or movement < 1e-3:
        raise SystemExit("固定原子漂移或自由原子未实际放松")
    rows = re.findall(
        r"^\s*FORCES\|\s+\d+\s+([-+0-9.Ee]+)\s+([-+0-9.Ee]+)\s+([-+0-9.Ee]+)\s+[-+0-9.Ee]+\s*$",
        text,
        re.MULTILINE,
    )
    forces = np.array(rows[-3:], dtype=float) * Hartree / Bohr
    if (
        forces.shape != (3, 3)
        or not np.isfinite(forces).all()
        or np.max(np.abs(forces[2])) > 0.024
    ):
        raise SystemExit("最终自由原子受力异常")
    result = {
        "max_frozen_drift_A": drift,
        "free_atom_displacement_A": movement,
        "free_atom_force_eV_A": forces[2].tolist(),
        "trajectory_frames": len(frames),
    }
    Path("selective-results.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))
    np.savetxt(
        "selective-displacements.dat",
        np.column_stack([np.arange(len(positions)), np.linalg.norm(delta, axis=2)]),
        header="frame displacement_O_A displacement_H1_A displacement_H2_A",
    )
    subprocess.run([sys.executable, "plot.py"], check=True)


if __name__ == "__main__":
    main()
