"""用法：python3 plot.py；Γ 点价带以各自价带顶对齐，不表示带色散。"""

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt


def main():
    data = json.loads(Path("soc-results.json").read_text())
    fig, ax = plt.subplots(figsize=(5, 3.8), layout="constrained")
    for x, stage in enumerate(["scalar", "soc"]):
        energies = data[stage]["gamma_valence_eigenvalues_eV"][2:8]
        for e in energies:
            ax.hlines(
                (e - max(energies)) * 1000,
                x - 0.18,
                x + 0.18,
                color=["tab:blue", "tab:orange"][x],
            )
    ax.set(
        xticks=[0, 1],
        xticklabels=["Without SOC", "With SOC"],
        ylabel="E − E(VBM, Γ) (meV)",
        title="Si | Γ-point valence splitting",
        xlim=(-0.5, 1.5),
    )
    ax.grid(axis="y", alpha=0.2)
    fig.savefig("si-soc.png", dpi=220)


if __name__ == "__main__":
    main()
