"""用法：python3 postprocess.py；比较网格或ADMM误差，检查能量与受力。"""

import json
import re
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

HARTREE_EV = 27.211386245988
result = {}
for stage in json.loads(Path("stages.json").read_text()):
    text = (Path(stage) / "cp2k.out").read_text()
    if (
        "PROGRAM ENDED AT" not in text
        or "SCF run converged" not in text
        or "SCF run NOT converged" in text
    ):
        raise SystemExit(f"{stage}未正常收敛")
    result[stage] = {
        "energy_hartree": float(
            re.findall(r"ENERGY\|.*?energy \[hartree\]\s+(-?[\d.]+)", text)[-1]
        )
    }
    rows = re.findall(r"^ FORCES\|\s+\d+\s+(\S+)\s+(\S+)\s+(\S+)", text, re.MULTILINE)
    force = np.array([[float(v) for v in row] for row in rows[-3:]])
    if force.shape != (3, 3) or not np.isfinite(force).all():
        raise SystemExit("受力数据异常")
    result[stage]["forces_hartree_bohr"] = force.tolist()
for stage in result:
    text = (Path(stage) / "cp2k.out").read_text()
    counts = re.findall(r"Number of electrons:\s*(\d+)", text)
    if not counts or int(counts[-1]) != 10:
        raise SystemExit("GAPW水分子应显式计算10个电子")
result["grid800_minus_grid400_eV"] = (
    result["grid800"]["energy_hartree"] - result["grid400"]["energy_hartree"]
) * HARTREE_EV
fig, ax = plt.subplots(figsize=(6, 3.7), layout="constrained")
ax.plot(
    [400, 800],
    [
        (result[s]["energy_hartree"] - result["grid800"]["energy_hartree"]) * HARTREE_EV
        for s in ["grid400", "grid800"]
    ],
    "o-",
)
ax.set(xlabel="Density-grid cutoff (Ry)", ylabel="Energy relative to 800 Ry (eV)")
fig.savefig("result.png", dpi=180)
Path("results.json").write_text(json.dumps(result, indent=2) + "\n")
print(json.dumps(result, indent=2))
