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
# 所有窗口必须相同组成；索引仅定义同一对溶质原子。
water_counts = [
    re.search(r"SOL\s+(\d+)", Path(s + ".top").read_text())[1] for s in stages
]
if len(set(water_counts)) != 1:
    raise SystemExit("窗口组成不一致，不能合并WHAM")
Path("tpr-files.dat").write_text("\n".join(s + "/md.tpr" for s in stages) + "\n")
Path("force-files.dat").write_text(
    "\n".join(s + "/md_pullf.xvg" for s in stages) + "\n"
)
with Path("wham.log").open("w") as out:
    subprocess.run(
        [
            exe,
            "wham",
            "-it",
            "tpr-files.dat",
            "-if",
            "force-files.dat",
            "-b",
            "2",
            "-e",
            "10",
            "-bins",
            "80",
            "-temp",
            "300",
            "-o",
            "pmf.xvg",
            "-hist",
            "histogram.xvg",
            "-xvg",
            "none",
        ],
        stdout=out,
        stderr=subprocess.STDOUT,
        check=True,
    )
profile = np.loadtxt("pmf.xvg")
finite = np.isfinite(profile[:, 1]) & (profile[:, 0] >= 0.35) & (profile[:, 0] <= 0.65)
profile = profile[finite]
if len(profile) < 30:
    raise SystemExit("有充分采样的PMF区间过短")
hist = np.loadtxt("histogram.xvg")
if hist.shape[1] != 6 or not np.isfinite(hist).all():
    raise SystemExit("WHAM直方图异常")
overlap = [float(np.minimum(hist[:, i], hist[:, i + 1]).sum()) for i in range(1, 5)]
if min(overlap) <= 0:
    raise SystemExit("相邻窗口无直方图重叠")
result = {
    "water_molecules": int(water_counts[0]),
    "sampled_PMF_range_nm": [float(profile[:, 0].min()), float(profile[:, 0].max())],
    "adjacent_histogram_overlap_counts": overlap,
}
fig, axs = plt.subplots(1, 2, figsize=(9, 3.7), layout="constrained")
axs[0].plot(hist[:, 0], hist[:, 1:])
axs[0].set(xlabel="Ar–Ar distance (nm)", ylabel="Histogram counts")
axs[1].plot(profile[:, 0], profile[:, 1] - profile[:, 1].min())
axs[1].set(xlabel="Ar–Ar distance (nm)", ylabel="PMF, arbitrary zero (kJ/mol)")
fig.savefig("result.png", dpi=180)
Path("results.json").write_text(json.dumps(result, indent=2) + "\n")
print(json.dumps(result, indent=2))
