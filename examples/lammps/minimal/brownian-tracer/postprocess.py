"""用法：python3 postprocess.py；将 Langevin 示踪粒子 MSD 与解析式比较。"""

import json
import subprocess
import sys
from pathlib import Path

import numpy as np

if "Total wall time:" not in Path("lammps.log").read_text():
    raise SystemExit("LAMMPS 未正常结束")
x = np.loadtxt("msd.dat")
if (
    x.shape != (2001, 3)
    or not np.isfinite(x).all()
    or not np.array_equal(x[:, 0], np.arange(0, 20001, 10))
):
    raise SystemExit("MSD 采样或时间轴异常")
time = x[:, 0] * 0.01
metrics = {}
for col, mass in [(1, 1), (2, 10)]:
    # kBT=gamma=1，damp=m/gamma；初始速度服从平衡 Maxwell 分布。
    theory = 6 * (time - mass * (1 - np.exp(-time / mass)))
    mask = time >= 30
    relative = np.sqrt(np.mean(((x[mask, col] - theory[mask]) / theory[mask]) ** 2))
    slope, intercept = np.polyfit(time[time >= 100], x[time >= 100, col], 1)
    if relative > 0.2 or slope <= 0:
        raise SystemExit("系综 MSD 与解析扩散响应偏差过大")
    metrics[f"mass_{mass}"] = {
        "particles": 512,
        "damping_time": mass,
        "friction": 1,
        "theoretical_D": 1,
        "late_fit_D": float(slope / 6),
        "late_rms_relative_error": float(relative),
    }
Path("brownian-results.json").write_text(json.dumps(metrics, indent=2) + "\n")
print(json.dumps(metrics, indent=2))
subprocess.run([sys.executable, "plot.py"], check=True)
