"""用法：python3 plot.py；比较两种质量的实际 MSD 与 Langevin 解析曲线。"""

import matplotlib.pyplot as plt
import numpy as np

x = np.loadtxt("msd.dat")
t = x[:, 0] * 0.01
fig, axes = plt.subplots(1, 2, figsize=(8.5, 3.5), layout="constrained")
for col, mass, color in [(1, 1, "#367dac"), (2, 10, "#b94e4e")]:
    theory = 6 * (t - mass * (1 - np.exp(-t / mass)))
    for ax in axes:
        ax.plot(t[1:], x[1:, col], color=color, label=f"m={mass} simulated")
        ax.plot(t[1:], theory[1:], "--", color=color, alpha=0.7)
axes[0].set(
    xlim=(0, 30),
    ylim=(0, 180),
    xlabel="Time / tau",
    ylabel="MSD / sigma^2",
    title="Early-time inertia",
)
axes[1].set(
    xlabel="Time / tau",
    ylabel="MSD / sigma^2",
    title="Same friction; same theoretical D",
)
axes[1].legend(fontsize=8)
for ax in axes:
    ax.grid(alpha=0.2)
fig.savefig("brownian-tracer.png", dpi=180)
