"""用法：python3 postprocess.py；调用原生WHAM/BAR，检查窗口并绘图。"""

import json
import re
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

HARTREE_EV = 27.211386245988
import os
import shutil
import subprocess

exe = shutil.which(os.environ.get("GMX_EXEC", "gmx"))
stages = json.loads(Path("stages.json").read_text())
for stage in stages:
    text = (Path(stage) / "md.log").read_text()
    if "Finished mdrun" not in text or re.search(
        r"LINCS WARNING|Fatal error|\bnan\b", text, re.IGNORECASE
    ):
        raise SystemExit(f"{stage}运行异常")
files = [s + "/md.xvg" for s in stages]
with Path("bar.log").open("w") as out:
    subprocess.run(
        [
            exe,
            "bar",
            "-f",
            *files,
            "-b",
            "2",
            "-e",
            "10",
            "-o",
            "bar.xvg",
            "-oi",
            "bar-integral.xvg",
            "-oh",
            "overlap.xvg",
            "-prec",
            "6",
            "-xvg",
            "none",
        ],
        stdout=out,
        stderr=subprocess.STDOUT,
        check=True,
    )
text = Path("bar.log").read_text()
summary = re.findall(
    r"total\s+\d+\s*-\s*\d+,\s+DG\s+(-?[\d.]+)\s+\+/-\s+([\d.]+)", text, re.IGNORECASE
)
if not summary:
    raise SystemExit("未读到原生BAR总自由能")
result = {
    "decoupling_DG_kJ_mol": float(summary[-1][0]),
    "native_block_error_kJ_mol": float(summary[-1][1]),
}
x = np.loadtxt("bar-integral.xvg")
if x.ndim != 2 or not np.isfinite(x).all():
    raise SystemExit("BAR积分数据异常")
fig, ax = plt.subplots(figsize=(6, 3.7), layout="constrained")
ax.plot(x[:, 0] / (len(stages) - 1), x[:, 1] * 0.00831446261815324 * 300, "o-")
ax.set(xlabel="Alchemical λ", ylabel="Cumulative decoupling free energy (kJ/mol)")
fig.savefig("result.png", dpi=180)
Path("results.json").write_text(json.dumps(result, indent=2) + "\n")
print(json.dumps(result, indent=2))
