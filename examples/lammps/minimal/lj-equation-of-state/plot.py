"""用法：python3 plot.py；绘制真实 LJ 晶格扫描。"""

import matplotlib.pyplot as plt
import numpy as np

x = np.loadtxt("scan.dat")
fig, axes = plt.subplots(1, 2, figsize=(8, 3.4), layout="constrained")
axes[0].plot(x[:, 1], x[:, 2], "o-")
axes[0].set(
    xlabel="Conventional lattice constant / sigma", ylabel="Energy / (N epsilon)"
)
axes[1].plot(x[:, 0], x[:, 3], "o-")
axes[1].axhline(0, color="gray", ls="--")
axes[1].set(xlabel="Reduced number density", ylabel="Pressure sigma^3 / epsilon")
for ax in axes:
    ax.grid(alpha=0.2)
fig.savefig("lj-eos.png", dpi=180)
