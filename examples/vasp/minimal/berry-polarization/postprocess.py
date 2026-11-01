"""用法：python3 postprocess.py；比较SOC方向或Berry相极化，保存物理单位。"""

import json
import re
from pathlib import Path

import matplotlib
from ase.io import read

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

HARTREE_EV = 27.211386245988

result = {}
for stage in json.loads(Path("stages.json").read_text()):
    text = (Path(stage) / "OUTCAR").read_text()
    if "General timing and accounting" not in text:
        raise SystemExit(f"{stage}未正常结束")
    atoms = read(Path(stage) / "vasprun.xml", format="vasp-xml")
    result[stage] = {"free_energy_eV": float(atoms.calc.results["free_energy"])}
cell = read("POSCAR", format="vasp").cell.array
volume = abs(np.linalg.det(cell))
dipoles = {}
for stage in result:
    text = (Path(stage) / "OUTCAR").read_text()
    electronic = re.findall(r"p\[elc\]=\s*\(?\s*([\d. -]+)", text)
    ionic = re.findall(r"p\[ion\]=\s*\(?\s*([\d. -]+)", text)
    if not electronic or not ionic:
        raise SystemExit("缺少Berry相偶极输出")
    dipoles[stage] = np.array(
        [float(v) for v in electronic[-1].split()[:3]]
    ) + np.array([float(v) for v in ionic[-1].split()[:3]])
reference = dipoles["zero"]
polarizations = []
for stage in ["minus", "zero", "plus"]:
    fraction = (dipoles[stage] - reference) @ np.linalg.inv(cell)
    # 极化量子为eR/Ω，对邻近小位移选择连续分支。
    fraction -= np.rint(fraction)
    delta = fraction @ cell
    result[stage]["delta_dipole_e_A"] = delta.tolist()
    result[stage]["delta_polarization_C_m2"] = (delta / volume * 16.02176634).tolist()
    polarizations.append(result[stage]["delta_polarization_C_m2"][2])
result["Born_Zzz_finite_difference_e"] = (
    result["plus"]["delta_dipole_e_A"][2] - result["minus"]["delta_dipole_e_A"][2]
) / 0.02
if not 0.1 < abs(result["Born_Zzz_finite_difference_e"]) < 10:
    raise SystemExit("Born有效电荷异常，请检查分支")
fig, ax = plt.subplots(figsize=(6, 3.7), layout="constrained")
ax.plot([-0.01, 0, 0.01], polarizations, "o-")
ax.set(
    xlabel="S displacement along z (Å)", ylabel="ΔPz (C/m²)", xticks=[-0.01, 0, 0.01]
)
fig.savefig("result.png", dpi=180)
Path("results.json").write_text(json.dumps(result, indent=2) + "\n")
print(json.dumps(result, indent=2))
