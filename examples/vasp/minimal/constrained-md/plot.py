"""用法：python3 plot.py；绘制实际轨迹中的 H—H 距离。"""

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

x = np.loadtxt("md-bond.dat")
constrained = Path("ICONST").read_text().split()[-1] == "0"
fig, ax = plt.subplots(figsize=(5.5, 3.5), layout="constrained")
ax.plot(x[:, 0], x[:, 1], "o-")
if constrained:
    ax.axhline(0.74, color="gray", ls="--")
    ax.set_ylim(0.739999, 0.740001)
ax.set(
    xlabel="Time (fs)",
    ylabel="H-H distance (Angstrom)",
    title="Constrained MD" if constrained else "Short metadynamics trajectory",
)
ax.ticklabel_format(useOffset=False, axis="y")
ax.grid(alpha=0.2)
fig.savefig("h2-md.png", dpi=180)
