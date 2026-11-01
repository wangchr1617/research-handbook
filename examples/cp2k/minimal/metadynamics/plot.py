"""用法：python3 plot.py；绘制实际 O—H 轨迹，增强采样例附最终偏置。"""

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

x = np.loadtxt("md-bond.dat")
constrained = "&CONSTRAINT" in Path("cp2k.inp").read_text()
fig, axes = plt.subplots(
    1,
    1 if constrained else 2,
    figsize=(5.5 if constrained else 8, 3.4),
    layout="constrained",
)
axes = np.atleast_1d(axes)
axes[0].plot(x[:, 0], x[:, 1], "o-")
axes[0].set(xlabel="Time (fs)", ylabel="O-H distance (Angstrom)")
axes[0].ticklabel_format(useOffset=False, axis="y")
if constrained:
    axes[0].set_ylim(x[0, 1] - 1e-6, x[0, 1] + 1e-6)
else:
    bias = np.loadtxt("final-bias.dat")
    axes[1].plot(bias[:, 0], bias[:, 1])
    axes[1].set(
        xlabel="O-H distance (Angstrom)",
        ylabel="Final bias (meV)",
        title="Three hills; not free energy",
    )
for ax in axes:
    ax.grid(alpha=0.2)
fig.savefig("water-md.png", dpi=180)
