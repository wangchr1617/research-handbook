"""用法：python3 plot.py；绘制固定几何水分子的静电场响应。"""

import matplotlib.pyplot as plt
import numpy as np

x = np.loadtxt("field-response.dat")
fig, axes = plt.subplots(1, 2, figsize=(8, 3.3), layout="constrained")
for ax, col, label in zip(axes, [1, 2], ["Energy shift (meV)", "Dipole y (Debye)"]):
    ax.plot(x[:, 0] * 1000, x[:, col], "o-")
    ax.set(xlabel="Field along y (10^-3 a.u.)", ylabel=label)
    ax.grid(alpha=0.2)
fig.savefig("water-field.png", dpi=180)
