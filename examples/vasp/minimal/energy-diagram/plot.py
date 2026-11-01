"""用法：python3 plot.py；守恒配平的 H2→2H* 电子能台阶，不是过渡态势垒。"""

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt


def main():
    d = json.loads(Path("energy-diagram-results.json").read_text())
    e = d["relative_energies_eV_cell"]
    fig, ax = plt.subplots(figsize=(7, 4), layout="constrained")
    for i, value in enumerate(e):
        ax.hlines(value, i - 0.3, i + 0.3, lw=3, color="tab:blue")
        ax.text(i, value + 0.035, f"{value:.3f} eV", ha="center")
        if i < 2:
            ax.plot([i + 0.3, i + 0.7], [value, e[i + 1]], "--", color=".6")
    ax.set(
        xticks=range(3),
        xticklabels=["* + H₂", "H* + ½H₂", "2H*"],
        ylabel="Relative electronic energy (eV / 2-site cell)",
        title="H/Al(111) | balanced electronic energy steps",
        ylim=(-0.1, max(e) + 0.18),
    )
    ax.grid(axis="y", alpha=0.2)
    fig.savefig("al-h-energy-diagram.png", dpi=220)


if __name__ == "__main__":
    main()
