"""用法：python3 plot.py；展示指定 H2 参考化学势区间内的候选态巨势下包络。"""

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


def main():
    a = np.loadtxt("surface-grand-potentials.dat")
    fig, ax = plt.subplots(figsize=(6.5, 4), layout="constrained")
    for i, label in enumerate(["Clean", "0.5 ML H", "1 ML H"], 1):
        ax.plot(a[:, 0], a[:, i] * 1000, label=label)
    ax.plot(
        a[:, 0],
        a[:, 1:4].min(axis=1) * 1000,
        color="k",
        ls="--",
        lw=2,
        label="Lower envelope",
    )
    ax.set(
        xlabel="Δμ(H) relative to ½E(H₂) (eV / H)",
        ylabel="Δsurface grand potential (meV/Å²)",
        title="H/Al(111) | one active surface",
    )
    ax.legend()
    ax.grid(alpha=0.2)
    fig.savefig("al-h-surface-phase.png", dpi=220)


if __name__ == "__main__":
    main()
