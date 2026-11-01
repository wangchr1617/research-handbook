"""用法：python3 plot.py；绘制 OUTCAR 提取的 Si K 边核吸收谱。"""

import matplotlib.pyplot as plt
import numpy as np

x = np.loadtxt("xas-spectrum.dat")
y = x[:, 2] / x[:, 2].max()
fig, ax = plt.subplots(figsize=(6.5, 3.8), layout="constrained")
ax.plot(x[:, 0], y, color="#296e9d")
# 聚焦存在信号的近边区域；不将计算能量平移成实验吸收边。
active = x[:, 0][y > 0.01]
ax.set_xlim(active.min() - 2, active.max() + 2)
ax.set(
    xlabel="Core-transition energy (eV)",
    ylabel="Normalized mean Im epsilon",
    title="Si K-edge: 8-atom XCH example",
)
ax.grid(alpha=0.2)
fig.savefig("si-xas.png", dpi=180)
