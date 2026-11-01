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
if "Freezing NCore=2" not in texts["mp2-fc"] or "Freezing NCore=2" in texts["mp2-all"]:
    raise SystemExit("冻结核设置与预期不一致")
result["correlation_eV"] = {
    name: (value - energies["hf"]) * HARTREE_EV
    for name, value in energies.items()
    if name != "hf"
}
if any(value >= 0 for value in result["correlation_eV"].values()):
    raise SystemExit("此水分子相关能异常")
fig, ax = plt.subplots(figsize=(6, 3.7), layout="constrained")
ax.bar(
    list(result["correlation_eV"]),
    list(result["correlation_eV"].values()),
    color="#3178a8",
)
ax.set(ylabel="Correlation energy relative to HF (eV)")
fig.savefig("result.png", dpi=180)
Path("results.json").write_text(json.dumps(result, indent=2) + "\n")
print(json.dumps(result, indent=2))
