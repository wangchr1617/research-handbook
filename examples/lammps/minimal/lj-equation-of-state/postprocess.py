"""用法：python3 postprocess.py；独立核对 fcc LJ 每原子能及密度换算。"""

import json
import subprocess
import sys
from pathlib import Path

import numpy as np
from ase.build import bulk
from ase.calculators.lj import LennardJones

x = np.loadtxt("scan.dat")
if (
    x.shape != (15, 4)
    or not np.isfinite(x).all()
    or not np.allclose(x[:, 1] ** 3 * x[:, 0], 4)
):
    raise SystemExit("扫描数据或 fcc 密度换算异常")
errors = []
for rho, alat, energy, pressure in x:
    atoms = bulk("Ar", "fcc", a=alat, cubic=True).repeat((4, 4, 4))
    atoms.calc = LennardJones(epsilon=1, sigma=1, rc=2.5)
    errors.append(abs(atoms.get_potential_energy() / len(atoms) - energy))
i = int(x[:, 2].argmin())
if max(errors) > 1e-8 or i in [0, len(x) - 1] or not (x[0, 3] < 0 < x[-1, 3]):
    raise SystemExit("独立 LJ 能量核对或极小值包围检查未通过")
# 仅对极小值附近五点拟合，避免用宽区间二次多项式代替状态方程。
c = np.polyfit(x[i - 2 : i + 3, 1], x[i - 2 : i + 3, 2], 2)
a0 = -c[1] / (2 * c[0])
metrics = {
    "atoms": 256,
    "points": len(x),
    "sample_minimum_a_sigma": float(x[i, 1]),
    "local_quadratic_a_sigma": float(a0),
    "minimum_energy_epsilon_per_atom": float(x[i, 2]),
    "max_ASE_crosscheck_error": max(errors),
}
Path("eos-results.json").write_text(json.dumps(metrics, indent=2) + "\n")
print(json.dumps(metrics, indent=2))
subprocess.run([sys.executable, "plot.py"], check=True)
