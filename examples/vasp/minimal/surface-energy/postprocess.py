"""用法：python3 postprocess.py；对称Al薄膜弛豫表面能与厚度线性拟合。"""

import json
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import numpy as np
from ase.io import read

EV_A2_TO_J_M2 = 16.02176634
for name in ["bulk", "slab4", "slab6", "slab8"]:
    subprocess.run(
        [sys.executable, str(Path("check_vasp.py").resolve())], cwd=name, check=True
    )
bulk = json.loads(Path("bulk/results.json").read_text())["energy_eV"]
rows = []
for n in [4, 6, 8]:
    work = Path(f"slab{n}")
    if "reached required accuracy" not in (work / "OUTCAR").read_text():
        raise SystemExit("薄膜几何未收敛")
    initial, final = read(work / "POSCAR"), read(work / "CONTCAR")
    delta = final.get_scaled_positions() - initial.get_scaled_positions()
    delta -= np.rint(delta)
    fixed = [n // 2 - 1, n // 2]
    if np.linalg.norm((delta @ initial.cell)[fixed], axis=1).max() > 1e-8:
        raise SystemExit("中间固定层发生位移")
    z = np.sort(final.positions[:, 2])
    if np.ptp(z + z[::-1]) > 1e-5:
        raise SystemExit("两表面弛豫后失去镜面对称")
    root = ET.parse(work / "vasprun.xml").getroot()
    steps = root.findall("calculation")
    energies = [float(c.find("energy/i[@name='e_0_energy']").text) for c in steps]
    force = np.array(
        [
            [float(v) for v in row.text.split()]
            for row in steps[-1].findall("varray[@name='forces']/v")
        ]
    )
    free = np.ones(n, dtype=bool)
    free[fixed] = False
    if np.abs(force[free, 2]).max() > 0.011:
        raise SystemExit("自由表层法向受力未达到阈值")
    area = np.linalg.norm(np.cross(initial.cell[0], initial.cell[1]))
    rows.append(
        [
            n,
            area,
            energies[0],
            energies[-1],
            (energies[0] - n * bulk) / (2 * area) * EV_A2_TO_J_M2,
            (energies[-1] - n * bulk) / (2 * area) * EV_A2_TO_J_M2,
        ]
    )
x = np.array(rows)
slope, intercept = np.polyfit(x[:, 0], x[:, 3], 1)
fit_gamma = intercept / (2 * x[0, 1]) * EV_A2_TO_J_M2
if (
    not np.isfinite(x).all()
    or not (x[:, 4:] > 0).all()
    or np.any(x[:, 3] > x[:, 2] + 1e-6)
):
    raise SystemExit("表面能数值或弛豫能量异常")
metrics = {
    "bulk_eV_atom": bulk,
    "rows_N_area_A2_Einitial_Erelaxed_gamma_initial_gamma_relaxed_J_m2": rows,
    "fit_bulk_eV_atom": float(slope),
    "fit_surface_energy_J_m2": float(fit_gamma),
    "fit_max_residual_eV": float(
        np.abs(x[:, 3] - np.polyval([slope, intercept], x[:, 0])).max()
    ),
}
Path("surface-results.json").write_text(json.dumps(metrics, indent=2) + "\n")
np.savetxt(
    "surface-energy.dat",
    x,
    header="N area_A2 E_initial_eV E_relaxed_eV gamma_initial_J_m2 gamma_relaxed_J_m2",
)
print(json.dumps(metrics, indent=2))
subprocess.run([sys.executable, "plot.py"], check=True)
