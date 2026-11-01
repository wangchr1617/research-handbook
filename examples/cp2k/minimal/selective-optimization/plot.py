"""用法：python3 plot.py；显示实际轨迹中各原子的位移。"""

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


def main():
    a = np.loadtxt("selective-displacements.dat")
    fig, ax = plt.subplots(figsize=(6, 3.8), layout="constrained")
    for i, label in enumerate(["O (fixed)", "H1 (fixed)", "H2 (free)"], 1):
        ax.plot(a[:, 0], a[:, i], marker=["o", "x", "s"][i - 1], label=label)
    ax.set(
        xlabel="Trajectory frame (0: input)",
        ylabel="Displacement (Å)",
        title="H₂O | constrained geometry optimization",
    )
    ax.legend()
    ax.grid(alpha=0.2)
    fig.savefig("water-selective.png", dpi=220)


if __name__ == "__main__":
    main()
