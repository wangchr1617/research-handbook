"""用法：python3 postprocess.py；比较SOC方向或Berry相极化，保存物理单位。"""

import json
import re
from pathlib import Path

import matplotlib
from ase.io import read

matplotlib.use("Agg")
import matplotlib.pyplot as plt

HARTREE_EV = 27.211386245988

result = {}
for stage in json.loads(Path("stages.json").read_text()):
    text = (Path(stage) / "OUTCAR").read_text()
    if "General timing and accounting" not in text:
        raise SystemExit(f"{stage}未正常结束")
    atoms = read(Path(stage) / "vasprun.xml", format="vasp-xml")
    result[stage] = {"free_energy_eV": float(atoms.calc.results["free_energy"])}
for stage, values in result.items():
    text = (Path(stage) / "OUTCAR").read_text()
    if not re.search(r"LSORBIT\s*=\s*T", text):
        raise SystemExit("未启用SOC")
    sections = text.split("magnetization (z)")
    if len(sections) < 2:
        raise SystemExit("缺少自旋投影")
    row = re.search(r"^\s*tot\s+([\d. -]+)$", sections[-1], re.MULTILINE)
    values["spin_projection_local_z_muB"] = float(row[1].split()[-1])
reference = result["z"]["free_energy_eV"]
for stage, values in result.items():
    values["delta_meV_vs_z"] = (values["free_energy_eV"] - reference) * 1000
fig, ax = plt.subplots(figsize=(6, 3.7), layout="constrained")
ax.bar(
    ["[001]", "[100]", "[010]"], [result[s]["delta_meV_vs_z"] for s in ["z", "x", "y"]]
)
ax.set(ylabel="SOC free energy relative to [001] (meV/2 Fe)")
fig.savefig("result.png", dpi=180)
Path("results.json").write_text(json.dumps(result, indent=2) + "\n")
print(json.dumps(result, indent=2))
