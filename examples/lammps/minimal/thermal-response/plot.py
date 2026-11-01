"""用法：python3 plot.py；实际NPT晶格常数与固定体积NVT能量，误差条为短块均值误差。"""

import matplotlib.pyplot as plt
import numpy as np

fig, axes = plt.subplots(1, 2, figsize=(8.5, 3.5), layout="constrained")
a = np.loadtxt("thermal.npt.dat")
e = np.loadtxt("thermal.nvt.dat")
axes[0].errorbar(a[:, 1], a[:, 3], yerr=a[:, 7], fmt="o-", capsize=3)
axes[0].set(
    xlabel="Measured temperature (K)",
    ylabel="Conventional a (Angstrom)",
    title="NPT at zero target pressure",
)
axes[1].errorbar(e[:, 1], e[:, 2], yerr=e[:, 6], fmt="o-", capsize=3)
axes[1].set(
    xlabel="Measured temperature (K)",
    ylabel="Total energy (eV/atom)",
    title="NVT at one fixed volume",
)
for ax in axes:
    ax.grid(alpha=0.2)
fig.savefig("cu-thermal-response.png", dpi=180)
