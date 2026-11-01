"""用法：python3 postprocess.py；检查自旋参考、O₂键长和电子解离能。"""

import json
import re
import subprocess
import sys
from pathlib import Path

import numpy as np
from ase.io import read

values = {}
for stage in ["atom-spin", "atom-nonspin", "molecule"]:
    work = Path(stage)
    subprocess.run(
        [sys.executable, str(Path("check_vasp.py").resolve())], cwd=work, check=True
    )
    if stage != "atom-nonspin":
        moments = re.findall(r"mag=\s*([-+0-9.]+)", (work / "OSZICAR").read_text())
        if not moments or abs(float(moments[-1]) - 2) > 1e-5:
            raise SystemExit("自旋参考未保持指定的 2 μB 总磁矩")
    values[stage] = json.loads((work / "results.json").read_text())["energy_eV"]
if "reached required accuracy" not in Path("molecule/OUTCAR").read_text():
    raise SystemExit("O₂结构未收敛")
length = read("molecule/CONTCAR").get_distance(0, 1, mic=True)
spin_lowering = values["atom-nonspin"] - values["atom-spin"]
dissociation = 2 * values["atom-spin"] - values["molecule"]
if (
    not np.isfinite([length, spin_lowering, dissociation]).all()
    or spin_lowering <= 0
    or dissociation <= 0
):
    raise SystemExit("自旋能量或解离能异常，请检查参考态")
metrics = {
    "energies_eV": values,
    "spin_stabilization_eV": spin_lowering,
    "O2_distance_A": length,
    "electronic_dissociation_eV": dissociation,
    "incorrect_nonspin_reference_eV": 2 * values["atom-nonspin"] - values["molecule"],
}
Path("oxygen-results.json").write_text(json.dumps(metrics, indent=2) + "\n")
print(json.dumps(metrics, indent=2))
subprocess.run([sys.executable, "plot.py"], check=True)
