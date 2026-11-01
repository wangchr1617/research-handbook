"""用法：python3 plot.py；绘制 Dimer 梯度与三个自由度的振动频率。"""

import matplotlib.pyplot as plt
import numpy as np

grad = np.atleast_1d(np.loadtxt("dimer-gradients.dat"))
freq = np.atleast_1d(np.loadtxt("dimer-frequencies.dat"))
fig, axes = plt.subplots(1, 2, figsize=(8, 3.4), layout="constrained")
axes[0].plot(np.arange(1, len(grad) + 1), grad, "o-")
axes[0].axhline(0.02, ls="--", color="gray")
axes[0].set(xlabel="Dimer gradient report", ylabel="Max gradient (eV/Angstrom)")
axes[1].bar(
    np.arange(1, 4), freq, color=["#b94e4e" if f < 0 else "#367dac" for f in freq]
)
axes[1].axhline(0, color="gray", lw=0.7)
axes[1].set(
    xlabel="Constrained vibrational mode",
    ylabel="Signed frequency (THz)",
    xticks=[1, 2, 3],
)
fig.savefig("si-dimer.png", dpi=180)
