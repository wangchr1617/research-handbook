"""用法：python3 plot.py；离散激发强度及高斯展宽谱，纵轴不是绝对吸收系数。"""

import matplotlib.pyplot as plt
import numpy as np

x = np.loadtxt("excitations.dat")
sigma_eV = 0.15  # 示意高斯展宽的标准差，eV，不代表计算得到的寿命。
grid = np.linspace(x[:, 1].min() - 0.7, x[:, 1].max() + 0.7, 800)
spectrum = (
    x[:, 5]
    * np.exp(-0.5 * ((grid[:, None] - x[:, 1]) / sigma_eV) ** 2)
    / (sigma_eV * np.sqrt(2 * np.pi))
).sum(axis=1)
fig, axes = plt.subplots(1, 2, figsize=(8, 3.4), layout="constrained")
axes[0].vlines(x[:, 1], 0, x[:, 5], color="#367dac")
axes[0].set(xlabel="Excitation energy (eV)", ylabel="Oscillator strength")
axes[1].plot(grid, spectrum)
axes[1].set(xlabel="Excitation energy (eV)", ylabel="Broadened intensity (1/eV)")
for ax in axes:
    ax.grid(alpha=0.2)
fig.savefig("water-excitations.png", dpi=180)
