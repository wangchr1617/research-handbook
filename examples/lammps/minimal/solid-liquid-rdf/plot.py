"""用法：python3 plot.py；实际 RDF 与 MSD 联合展示。"""

import matplotlib.pyplot as plt
import numpy as np

fig, axes = plt.subplots(1, 2, figsize=(8, 3.5), layout="constrained")
for state, label in [("solid", "T*=0.2"), ("liquid", "T*=1.5")]:
    rdf = np.loadtxt(f"rdf-mean.{state}.dat")
    msd = np.loadtxt(f"msd.{state}.dat")
    axes[0].plot(rdf[:, 0], rdf[:, 1], label=label)
    axes[1].plot(msd[:, 0] * 0.005, msd[:, 1], label=label)
axes[0].set(xlabel="r / sigma", ylabel="g(r)")
axes[1].set(xlabel="Time / tau", ylabel="MSD / sigma^2")
for ax in axes:
    ax.legend()
    ax.grid(alpha=0.2)
fig.savefig("solid-liquid-rdf.png", dpi=180)
