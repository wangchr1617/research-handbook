"""用法：python3 plot.py；绘制真实层数对照与体相参考差异。"""

import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

x = np.loadtxt("surface-energy.dat")
m = json.loads(Path("surface-results.json").read_text())
fig, ax = plt.subplots(figsize=(6.2, 3.8), layout="constrained")
ax.plot(x[:, 0], x[:, 4], "o--", label="Ideal slab; bulk reference")
ax.plot(x[:, 0], x[:, 5], "o-", label="Relaxed slab; bulk reference")
ax.axhline(
    m["fit_surface_energy_J_m2"], color="gray", ls=":", label="Relaxed thickness fit"
)
ax.set(xlabel="Al(111) layers", ylabel="Surface energy (J/m^2)", xticks=[4, 6, 8])
ax.legend(fontsize=8)
ax.grid(alpha=0.2)
fig.savefig("al-surface-energy.png", dpi=180)
