"""用法：python3 plot.py；显示第2原子的分数坐标位移。"""

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


def main():
    a = np.loadtxt("fractional-displacements.dat")
    fig, ax = plt.subplots(figsize=(6, 3.8), layout="constrained")
    for i, label in enumerate(["s1 (fixed)", "s2 (fixed)", "s3 (free)"], 1):
        ax.plot(a[:, 0], a[:, i], marker=["o", "x", "s"][i - 1], label=label)
    ax.set(
        xlabel="Ionic step (0: input)",
        ylabel="Fractional displacement",
        title="Si | selective dynamics",
    )
    ax.legend()
    ax.grid(alpha=0.2)
    fig.savefig("si-selective.png", dpi=220)


if __name__ == "__main__":
    main()
