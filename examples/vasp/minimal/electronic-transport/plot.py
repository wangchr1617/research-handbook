"""用法：python3 plot.py；绘制 BoltzTraP2 的电子热导率除以弛豫时间。"""

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from ase.units import Rydberg


def main():
    metrics = json.loads(Path("transport-results.json").read_text())
    table = np.loadtxt("interpolation.trace")
    x = table[:, 0] * Rydberg - metrics["reference_energy_eV"]
    limit = metrics["energy_window_eV"]
    fig, ax = plt.subplots(figsize=(6.0, 4.2), constrained_layout=True)
    for temperature, color in zip(metrics["temperatures_K"], ["#24618c", "#a54828"]):
        mask = (table[:, 1] == temperature) & (np.abs(x) <= limit)
        ax.semilogy(x[mask], table[mask, 7], color=color, label=f"{temperature:g} K")
    ax.axvline(0, color="0.5", linewidth=0.8, linestyle="--")
    ax.set(
        xlabel=r"$\mu-\mu_{\mathrm{ref}}$ (eV)",
        ylabel=r"$\kappa_e/\tau$ (W m$^{-1}$ K$^{-1}$ s$^{-1}$)",
        title="Si | constant relaxation time",
        xlim=(-limit, limit),
    )
    ax.legend(frameon=False)
    ax.grid(alpha=0.2)
    fig.savefig(
        "si-electronic-transport.png", dpi=240, bbox_inches="tight", facecolor="white"
    )
    plt.close(fig)
    print("已生成 si-electronic-transport.png")


if __name__ == "__main__":
    main()
