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
reference = result["full"]["energy_hartree"]
errors = [
    (result[s]["energy_hartree"] - reference) * HARTREE_EV for s in ["cfit3", "fit3"]
]
for stage, error in zip(["cfit3", "fit3"], errors):
    result[stage]["delta_energy_eV_vs_full"] = error
    result[stage]["max_force_error_eV_A"] = float(
        np.max(
            abs(
                np.array(result[stage]["forces_hartree_bohr"])
                - np.array(result["full"]["forces_hartree_bohr"])
            )
        )
        * HARTREE_EV
        / 0.529177210903
    )
fig, ax = plt.subplots(figsize=(6, 3.7), layout="constrained")
ax.bar(["cFIT3", "FIT3"], errors)
ax.set(ylabel="ADMM − full HFX energy (eV)")
fig.savefig("result.png", dpi=180)
Path("results.json").write_text(json.dumps(result, indent=2) + "\n")
print(json.dumps(result, indent=2))
