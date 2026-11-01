"""用法：python3 postprocess.py；检查原生ORCA结果，提取目标量与绘图。"""

import json
import re
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

HARTREE_EV = 27.211386245988
texts = {}
energies = {}
for stage in json.loads(Path("stages.json").read_text()):
    text = (Path(stage) / "orca.out").read_text()
    if "ORCA TERMINATED NORMALLY" not in text or "SCF NOT CONVERGED" in text:
        raise SystemExit(f"{stage}未正常收敛")
    texts[stage] = text
    energies[stage] = float(
        re.findall(r"FINAL SINGLE POINT ENERGY\s+(-?[\d.]+)", text)[-1]
    )
result = {"energies_hartree": energies}
section = texts["shielding"].split("CHEMICAL SHIELDING SUMMARY (ppm)")[-1]
rows = re.findall(
    r"^\s*(\d+)\s+([A-Z][a-z]?)\s+(-?[\d.]+)\s+(-?[\d.]+)\s*$", section, re.MULTILINE
)
if len(rows) != 3:
    raise SystemExit("未找到三个核的屏蔽值")
result["shieldings_ppm"] = [
    {
        "index": int(i),
        "element": element,
        "isotropic": float(iso),
        "anisotropy": float(aniso),
    }
    for i, element, iso, aniso in rows
]
fig, ax = plt.subplots(figsize=(6, 3.7), layout="constrained")
ax.bar(
    [element + str(i) for i, element, _, _ in rows],
    [float(v) for _, _, v, _ in rows],
    color="#3178a8",
)
ax.set(ylabel="Isotropic shielding (ppm)")
fig.savefig("result.png", dpi=180)
Path("results.json").write_text(json.dumps(result, indent=2) + "\n")
print(json.dumps(result, indent=2))
