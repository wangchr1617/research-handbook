"""用法：python3 postprocess.py；提取响应系数，检查物理定义并绘图。"""

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

HARTREE_EV = 27.211386245988
if "Total wall time:" not in Path("lammps.out").read_text():
    raise SystemExit("LAMMPS未正常结束")
lines = [
    line
    for line in Path("correlation.dat").read_text().splitlines()
    if not line.startswith("#")
]
blocks = []
i = 0
while i < len(lines):
    header = lines[i].split()
    i += 1
    if len(header) != 2:
        raise SystemExit("自相关块格式异常")
    count = int(header[1])
    blocks.append(
        np.array([[float(v) for v in line.split()] for line in lines[i : i + count]])
    )
    i += count
x = blocks[-1]
if x.shape != (200, 6) or not np.isfinite(x).all() or np.any(x[:, 2] <= 0):
    raise SystemExit("自相关计数或数据异常")
lag = x[:, 1] * 0.005
corr = x[:, 3:6]
temperature = np.loadtxt("temperature.dat")[:, 1].mean()
volume = float(Path("volume.dat").read_text())
# LJ约化单位下kB=1；压力相关函数的体积因子不可遗漏。
eta = (
    np.vstack(
        [
            np.zeros(3),
            np.cumsum((corr[1:] + corr[:-1]) * np.diff(lag)[:, None] / 2, axis=0),
        ]
    )
    * volume
    / temperature
)
result = {
    "mean_temperature_reduced": float(temperature),
    "correlation_time_reduced": float(lag[-1]),
    "running_viscosity_components_reduced": eta[-1].tolist(),
    "running_viscosity_average_reduced": float(eta[-1].mean()),
}
np.savetxt(
    "viscosity.dat",
    np.column_stack([lag, eta, eta.mean(axis=1)]),
    header="lag_tau eta_xy eta_xz eta_yz eta_mean",
)
fig, axs = plt.subplots(1, 2, figsize=(9, 3.7), layout="constrained")
axs[0].plot(lag, corr)
axs[0].set(xlabel="Lag time (τ)", ylabel="Pressure autocorrelation (ε²/σ⁶)")
axs[1].plot(lag, eta, alpha=0.5)
axs[1].plot(lag, eta.mean(axis=1), color="black", label="Mean")
axs[1].set(xlabel="Integration limit (τ)", ylabel="Running viscosity (ετ/σ³)")
axs[1].legend()
fig.savefig("result.png", dpi=180)
Path("results.json").write_text(json.dumps(result, indent=2) + "\n")
print(json.dumps(result, indent=2))
