"""用法：python3 plot.py；比较不同温度下的实际全对距离涨落。"""

import matplotlib.pyplot as plt
import numpy as np

fig, ax = plt.subplots(figsize=(6, 3.6), layout="constrained")
for state, label in [("cold", "T*=0.05"), ("warm", "T*=0.30")]:
    x = np.loadtxt(f"lindemann.{state}.dat")
    ax.plot(x[:, 0], x[:, 1], label=label)
ax.set(xlabel="Sampling time / tau", ylabel="Running all-pair Lindemann index")
ax.legend()
ax.grid(alpha=0.2)
fig.savefig("cluster-lindemann.png", dpi=180)
