"""用法：python3 plot.py；绘制截断能和 k 网格扫描的相对每原子能量。"""

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


def main():
    result = json.loads(Path("convergence-results.json").read_text())
    fig, axes = plt.subplots(1, 2, figsize=(8, 3.5), constrained_layout=True)
    for ax, key, xkey, label in [
        (axes[0], "cutoff_points", "cutoff_eV", "Cutoff (eV)"),
        (axes[1], "k_points", "k_mesh", r"$n$ in $n\times n\times n$ k mesh"),
    ]:
        points = result[key]
        energies = np.array([p["energy_eV_atom"] for p in points])
        ax.plot(
            [p[xkey] for p in points],
            (energies - energies[-1]) * 1000,
            "o-",
            color="#24618c",
        )
        ax.set(xlabel=label, ylabel=r"$E-E_{\mathrm{last}}$ (meV/atom)")
        ax.grid(alpha=0.2)
    axes[0].set_title("Si | fixed k mesh 7 cubed")
    axes[1].set_title("Si | fixed cutoff 450 eV")
    fig.savefig("si-convergence.png", dpi=240, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print("已生成 si-convergence.png")


if __name__ == "__main__":
    main()
