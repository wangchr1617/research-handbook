"""用法：python3 plot.py；实际 MSD 与两个窗口的线性拟合。"""

import matplotlib.pyplot as plt
import numpy as np

x = np.loadtxt("msd-plot.dat")
fig, ax = plt.subplots(figsize=(6, 3.8), layout="constrained")
ax.plot(x[:, 0], x[:, 1], label="LJ liquid MSD")
for start, stop in [(10, 30), (20, 50)]:
    m = (x[:, 0] >= start) & (x[:, 0] <= stop)
    c = np.polyfit(x[m, 0], x[m, 1], 1)
    ax.plot(x[m, 0], np.polyval(c, x[m, 0]), "--", label=f"Fit {start}-{stop}")
ax.set(xlabel="Time / tau", ylabel="MSD / sigma^2")
ax.legend()
ax.grid(alpha=0.2)
fig.savefig("lj-diffusion.png", dpi=180)
