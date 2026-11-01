"""用法：python3 plot.py；读取 VTST neb.dat，绘制实际插点的相对能量。"""

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


def main():
    data = np.loadtxt("neb.dat")
    fig, ax = plt.subplots(figsize=(5.8, 4.0), constrained_layout=True)
    ax.plot(data[:, 1], data[:, 2], "o-", color="#24618c", markersize=5, linewidth=1.2)
    ax.set(
        xlabel=r"Path length ($\AA$)",
        ylabel="Relative energy (eV)",
        title="Constrained Si hop | CI-NEB (VASP)",
    )
    fig.savefig("si-neb-vasp.png", dpi=240, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print("已生成 si-neb-vasp.png")


if __name__ == "__main__":
    main()
