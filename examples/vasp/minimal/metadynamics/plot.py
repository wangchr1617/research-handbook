"""用法：python3 plot.py；绘制短轨迹和实际 HILLSPOT 重建的最终偏置。"""

import matplotlib.pyplot as plt
import numpy as np

x = np.loadtxt("md-bond.dat")
bias = np.loadtxt("final-bias.dat")
fig, axes = plt.subplots(1, 2, figsize=(8, 3.4), layout="constrained")
axes[0].plot(x[:, 0], x[:, 1], "o-")
axes[0].set(xlabel="Time (fs)", ylabel="H-H distance (Angstrom)")
axes[1].plot(bias[:, 0], bias[:, 1] * 1000)
axes[1].set(
    xlabel="H-H distance (Angstrom)",
    ylabel="Final bias (meV)",
    title="Four hills; not a free-energy profile",
)
for ax in axes:
    ax.grid(alpha=0.2)
fig.savefig("h2-md.png", dpi=180)
