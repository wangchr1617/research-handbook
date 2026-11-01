"""用法：python3 plot.py；分别以各自费米能对齐，上下自旋镜像显示。"""

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


def main():
    fig, axes = plt.subplots(2, 1, figsize=(6, 5.2), sharex=True, layout="constrained")
    for ax, stage, label in zip(
        axes, ["u0", "u4"], ["Ueff = 0 eV", "Ueff = 4 eV"], strict=True
    ):
        a = np.loadtxt(f"{stage}/TDOS.dat")
        ax.plot(a[:, 0], np.abs(a[:, 1]), label="↑")
        ax.plot(a[:, 0], -np.abs(a[:, 2]), label="↓")
        ax.axvline(0, color=".5", ls="--")
        ax.set(title=label, ylabel="DOS (states/eV/cell)", xlim=(-8, 6))
        ax.legend()
        ax.grid(alpha=0.2)
    axes[1].set_xlabel("E − E(F) (eV)")
    fig.savefig("nio-hubbard-dos.png", dpi=220)


if __name__ == "__main__":
    main()
