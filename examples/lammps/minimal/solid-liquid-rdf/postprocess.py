"""用法：python3 postprocess.py；读取 RDF 分块记录并结合 MSD 比较固液结构。"""

import json
import subprocess
import sys
from pathlib import Path

import numpy as np

if "Total wall time:" not in Path("lammps.log").read_text():
    raise SystemExit("LAMMPS 未正常结束")
metrics = {}
for state in ["solid", "liquid"]:
    lines = [
        line
        for line in Path(f"rdf.{state}.dat").read_text().splitlines()
        if line.strip() and not line.startswith("#")
    ]
    blocks = []
    i = 0
    while i < len(lines):
        step, count = map(int, lines[i].split())
        block = np.array(
            [[float(v) for v in line.split()] for line in lines[i + 1 : i + 1 + count]]
        )
        if count != 80 or block.shape != (80, 4):
            raise SystemExit("RDF 分块不完整")
        blocks.append(block)
        i += count + 1
    if len(blocks) != 10 or not np.isfinite(blocks).all():
        raise SystemExit("RDF 采样窗口不足或含非有限值")
    mean = np.mean(blocks, axis=0)
    if not np.array_equal(mean[:, 0], np.arange(1, 81)) or np.any(mean[:, 2:] < 0):
        raise SystemExit("RDF 网格或非负性异常")
    msd = np.loadtxt(f"msd.{state}.dat")
    if msd.shape != (51, 2) or not np.array_equal(msd[:, 0], np.arange(0, 5001, 100)):
        raise SystemExit("MSD 时间轴不完整")
    np.savetxt(f"rdf-mean.{state}.dat", mean[:, 1:], header="r_sigma g_r coordination")
    metrics[state] = {
        "rdf_blocks": len(blocks),
        "first_peak_r_sigma": float(mean[np.argmax(mean[:, 2]), 1]),
        "last_MSD_sigma2": float(msd[-1, 1]),
    }
if not (
    metrics["solid"]["last_MSD_sigma2"] < 0.2
    and metrics["liquid"]["last_MSD_sigma2"] > 5 * metrics["solid"]["last_MSD_sigma2"]
):
    raise SystemExit("两种状态未表现出预期的振动/扩散差异")
Path("phase-results.json").write_text(json.dumps(metrics, indent=2) + "\n")
print(json.dumps(metrics, indent=2))
subprocess.run([sys.executable, "plot.py"], check=True)
