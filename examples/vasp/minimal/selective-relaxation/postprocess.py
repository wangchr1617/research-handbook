"""用法：python3 postprocess.py；核对整条轨迹中冻结分量与自由方向的实际变化。"""

import json
import subprocess
import sys
from pathlib import Path

import numpy as np
from ase.io import read


def main():
    subprocess.run([sys.executable, "check_vasp.py"], check=True)
    if "reached required accuracy" not in Path("OUTCAR").read_text(errors="replace"):
        raise SystemExit("选择性优化未收敛")
    initial = read("POSCAR")
    frames = read("vasprun.xml", index=":")
    coords = np.array(
        [initial.get_scaled_positions(wrap=False)]
        + [a.get_scaled_positions(wrap=False) for a in frames]
    )
    delta = coords - coords[0]
    delta -= np.rint(delta)
    # T/F 定义相对于晶格方向；这里仅第2原子的第3个分量可变。
    frozen = np.ones((2, 3), dtype=bool)
    frozen[1, 2] = False
    error = float(np.max(np.abs(delta[:, frozen])))
    if error > 1e-8 or abs(delta[-1, 1, 2]) < 1e-3:
        raise SystemExit("冻结分量漂移或自由分量未实际放松")
    force = frames[-1].get_forces(apply_constraint=False)[1]
    direction = initial.cell.array[2] / np.linalg.norm(initial.cell.array[2])
    projected = abs(float(force @ direction))
    if projected > 0.011:
        raise SystemExit("自由方向投影受力尚未收敛")
    Path("selective-results.json").write_text(
        json.dumps(
            {
                "steps": len(frames),
                "max_frozen_fractional_drift": error,
                "free_fractional_change": float(delta[-1, 1, 2]),
                "free_force_eV_A": projected,
            },
            indent=2,
        )
        + "\n"
    )
    np.savetxt(
        "fractional-displacements.dat",
        np.column_stack([np.arange(len(coords)), delta[:, 1, :]]),
        header="step delta_s1 delta_s2 delta_s3",
    )
    subprocess.run([sys.executable, "plot.py"], check=True)


if __name__ == "__main__":
    main()
