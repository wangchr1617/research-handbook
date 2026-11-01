"""用法：python3 postprocess.py；检查原生ORCA结果，提取目标量与绘图。"""

import json
import re
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

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
occupation = {}
for stage, text in texts.items():
    if stage.startswith("cas"):
        if "THE CAS-SCF GRADIENT HAS CONVERGED" not in text:
            raise SystemExit("CASSCF轨道梯度未收敛")
        section = text.rsplit("ORBITAL ENERGIES", 1)[-1]
        rows = re.findall(
            r"^\s*\d+\s+(\d+\.\d+)\s+-?[\d.]+\s+-?[\d.]+\s*$", section, re.MULTILINE
        )
        occupation[stage] = [float(v) for v in rows[:2]]
        if len(occupation[stage]) != 2 or abs(sum(occupation[stage]) - 2) > 1e-3:
            raise SystemExit("活性轨道占据解析异常")
result["active_occupations"] = occupation
fig, axs = plt.subplots(1, 2, figsize=(9, 3.7), layout="constrained")
lengths = [0.74, 1.5, 3.0]
for method, label in [("rhf", "RHF"), ("cas", "CASSCF(2,2)")]:
    e = np.array([energies[method + "-" + s] for s in ["074", "150", "300"]])
    axs[0].plot(lengths, (e - energies["cas-074"]) * HARTREE_EV, "o-", label=label)
axs[0].set(xlabel="H–H distance (Å)", ylabel="Energy relative to CAS at 0.74 Å (eV)")
axs[0].legend()
occ = np.array([occupation["cas-" + s] for s in ["074", "150", "300"]])
axs[1].plot(lengths, occ, "o-")
axs[1].set(
    xlabel="H–H distance (Å)", ylabel="Active natural-orbital occupation", ylim=(0, 2)
)
fig.savefig("result.png", dpi=180)
Path("results.json").write_text(json.dumps(result, indent=2) + "\n")
print(json.dumps(result, indent=2))
