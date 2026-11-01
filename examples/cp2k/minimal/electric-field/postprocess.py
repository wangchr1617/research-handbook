"""用法：python3 postprocess.py；提取正负电场的能量、偶极与有限差分响应。"""

import json
import re
import subprocess
import sys
from pathlib import Path

import numpy as np

FIELD_AU = 0.001  # 电场原子单位，约 0.05142 V/Å；与三份输入一致。
DEBYE_PER_AU = 2.541746473

values = {}
for name in ["minus", "zero", "plus"]:
    work = Path(name)
    subprocess.run(
        [sys.executable, str(Path("check_cp2k.py").resolve())], cwd=work, check=True
    )
    result = json.loads((work / "results.json").read_text())
    text = (work / "cp2k.out").read_text()
    match = re.search(
        r"Dipole moment \[Debye\]\s*X=\s*([-+0-9.Ee]+)\s*Y=\s*([-+0-9.Ee]+)\s*Z=\s*([-+0-9.Ee]+)",
        text,
    )
    if not match:
        raise SystemExit("未找到完整偶极输出，请开启 MOMENTS ON")
    dipole = np.array([float(v) for v in match.groups()])
    if not np.isfinite(dipole).all():
        raise SystemExit("偶极含非有限值")
    values[name] = {
        "energy_Hartree": result["energy_Hartree"],
        "dipole_Debye": dipole.tolist(),
    }
e = np.array([values[n]["energy_Hartree"] for n in values])
mu = np.array([values[n]["dipole_Debye"][1] for n in values]) / DEBYE_PER_AU
mu_energy = -(e[2] - e[0]) / (2 * FIELD_AU)
alpha_mu = (mu[2] - mu[0]) / (2 * FIELD_AU)
alpha_energy = -(e[2] - 2 * e[1] + e[0]) / FIELD_AU**2
if (
    alpha_mu <= 0
    or abs(mu_energy - mu[1]) > 0.002
    or not np.isclose(alpha_mu, alpha_energy, rtol=0.03)
):
    raise SystemExit("能量导数与偶极响应不一致，请检查场方向、单位和 SCF")
metrics = {
    "states": values,
    "mu_from_energy_au": float(mu_energy),
    "alpha_yy_from_dipole_au": float(alpha_mu),
    "alpha_yy_from_energy_au": float(alpha_energy),
}
Path("field-results.json").write_text(json.dumps(metrics, indent=2) + "\n")
np.savetxt(
    "field-response.dat",
    np.column_stack(
        [
            [-FIELD_AU, 0, FIELD_AU],
            (e - e[1]) * 27.211386245988 * 1000,
            mu * DEBYE_PER_AU,
        ]
    ),
    header="field_au energy_shift_meV dipole_y_Debye",
)
print(json.dumps(metrics, indent=2))
subprocess.run([sys.executable, "plot.py"], check=True)
