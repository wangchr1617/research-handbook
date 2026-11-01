"""用法：python3 postprocess.py；核对水分子短 MD 的轨迹、SCF 与集体变量。"""

import json
import re
import subprocess
import sys
from pathlib import Path

import numpy as np
from ase.io import read
from ase.units import Bohr

text = Path("cp2k.out").read_text()
if (
    "PROGRAM ENDED AT" not in text
    or "SCF run NOT converged" in text
    or text.count("SCF run converged") != 7
):
    raise SystemExit("MD 未完成或逐步 SCF 不完整")
energy = np.loadtxt("water-1.ener", ndmin=2)
frames = read("water-pos-1.xyz", index=":")
if len(frames) != 7 or energy.shape[0] != 7 or not np.isfinite(energy).all():
    raise SystemExit("需要初始帧及六个 MD 步")
if not np.array_equal(energy[:, 0], np.arange(7)) or not np.allclose(
    energy[:, 1], np.arange(7) * 0.5
):
    raise SystemExit("MD 时间轴异常")
bonds = np.array([a.get_distance(0, 1) for a in frames])
constrained = "&CONSTRAINT" in Path("cp2k.inp").read_text()
metrics = {
    "steps": 6,
    "frames": 7,
    "bond_interval_A": [float(bonds.min()), float(bonds.max())],
}
if constrained:
    target = (
        float(re.search(r"TARGET\s+([0-9.]+)", Path("cp2k.inp").read_text())[1]) * Bohr
    )
    drift = float(np.abs(bonds - target).max())
    if (
        drift > 1e-7
        or "Number of intermolecular constraints                                     1"
        not in text
    ):
        raise SystemExit("约束未生效或距离误差过大")
    metrics.update(target_A=target, max_bond_error_A=drift)
else:
    colvars = np.vstack(
        [np.loadtxt(f, ndmin=2) for f in Path(".").glob("water-COLVAR*.metadynLog")]
    )
    colvars = colvars[np.argsort(colvars[:, 0])]
    hills = np.vstack(
        [np.loadtxt(f, ndmin=2) for f in Path(".").glob("water-HILLS*.metadynLog")]
    )
    hills = hills[np.argsort(hills[:, 0])]
    if colvars.shape != (7, 6) or hills.shape != (3, 4) or not np.isfinite(hills).all():
        raise SystemExit("COLVAR 或高斯丘记录不完整")
    if not np.allclose(colvars[:, 0], energy[:, 1]) or not np.allclose(
        colvars[:, 1] * Bohr, bonds, atol=4e-6
    ):
        raise SystemExit("集体变量与真实轨迹不一致")
    if not np.allclose(hills[:, 0], [1, 2, 3]) or not np.allclose(
        hills[:, 2:], [0.05, 0.0002]
    ):
        raise SystemExit("高斯丘时间、宽度或高度与输入不一致")
    grid = np.linspace(hills[:, 1].min() - 0.2, hills[:, 1].max() + 0.2, 400)
    bias = (
        hills[:, 3] * np.exp(-0.5 * ((grid[:, None] - hills[:, 1]) / hills[:, 2]) ** 2)
    ).sum(axis=1)
    np.savetxt(
        "final-bias.dat",
        np.column_stack([grid * Bohr, bias * 27.211386245988 * 1000]),
        header="distance_A bias_meV",
    )
    metrics["hills_time_fs_center_bohr_width_bohr_height_Ha"] = hills.tolist()
np.savetxt(
    "md-bond.dat", np.column_stack([energy[:, 1], bonds]), header="time_fs bond_A"
)
Path("md-results.json").write_text(json.dumps(metrics, indent=2) + "\n")
print(json.dumps(metrics, indent=2))
subprocess.run([sys.executable, "plot.py"], check=True)
