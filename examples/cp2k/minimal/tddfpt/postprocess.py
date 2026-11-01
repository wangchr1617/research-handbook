"""用法：python3 postprocess.py；提取单重激发能和振子强度并绘制示意谱。"""

import json
import re
import subprocess
import sys
from pathlib import Path

import numpy as np

text = Path("cp2k.out").read_text()
if (
    "PROGRAM ENDED AT" not in text
    or "SCF run converged" not in text
    or "SCF run NOT converged" in text
    or "TDDFPT run converged" not in text
):
    raise SystemExit("基态或 TDDFPT 未正常收敛")
rows = re.findall(
    r"^\s*TDDFPT\|\s+(\d+)\s+([-+]?[0-9]+(?:\.[0-9]*)?(?:[Ee][-+]?[0-9]+)?)\s+([-+]?[0-9]+(?:\.[0-9]*)?(?:[Ee][-+]?[0-9]+)?)\s+([-+]?[0-9]+(?:\.[0-9]*)?(?:[Ee][-+]?[0-9]+)?)\s+([-+]?[0-9]+(?:\.[0-9]*)?(?:[Ee][-+]?[0-9]+)?)\s+([-+]?[0-9]+(?:\.[0-9]*)?(?:[Ee][-+]?[0-9]+)?)\s*$",
    text,
    re.MULTILINE,
)
data = np.array(rows, dtype=float)
if (
    data.shape != (3, 6)
    or not np.isfinite(data).all()
    or not np.array_equal(data[:, 0], [1, 2, 3])
):
    raise SystemExit("三个激发态的输出不完整")
if (
    not (data[:, 1] > 0).all()
    or not (np.diff(data[:, 1]) > 0).all()
    or not (data[:, 5] >= 0).all()
):
    raise SystemExit("激发能或振子强度异常")
if "states of multiplicity 1" not in text:
    raise SystemExit("需确认当前输出为单重激发态")
np.savetxt(
    "excitations.dat",
    data,
    header="state energy_eV dipole_x_au dipole_y_au dipole_z_au oscillator_strength",
)
metrics = {
    "singlet_energies_eV": data[:, 1].tolist(),
    "oscillator_strengths": data[:, 5].tolist(),
    "multiplicity": 1,
}
Path("excitation-results.json").write_text(json.dumps(metrics, indent=2) + "\n")
print(json.dumps(metrics, indent=2))
subprocess.run([sys.executable, "plot.py"], check=True)
