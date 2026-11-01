"""用法：python3 plot.py；显示 Γ 点准粒子修正，统一以 PBE Γ 点价带顶为参考。"""

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


def main():
    a = np.loadtxt("quasiparticles.dat")
    all_points = a.copy()
    a = a[a[:, 0] == 1]
    reference = a[a[:, 8] > 1, 2].max()
    fig, axes = plt.subplots(1, 2, figsize=(10, 4), layout="constrained")
    ax = axes[0]
    ax.plot(a[:, 1], a[:, 2] - reference, "o-", label="PBE")
    ax.plot(a[:, 1], a[:, 3] - reference, "s-", label="G₀W₀")
    ax.axhline(0, color=".5", ls=":")
    ax.set(
        xlabel="Band index at Γ",
        ylabel="Energy relative to PBE VBM at Γ (eV)",
        title="Si | coarse GW demonstration",
    )
    ax.legend()
    ax.grid(alpha=0.2)
    other = axes[1]
    for column, marker, label, offset in [
        (2, "+", "PBE", -0.04),
        (3, "o", "G₀W₀", 0.04),
    ]:
        selected = all_points[(all_points[:, 1] >= 2) & (all_points[:, 1] <= 8)]
        other.scatter(
            selected[:, 0] + offset,
            selected[:, column] - reference,
            marker=marker,
            label=label,
            s=22,
        )
    other.set(
        xlabel="Irreducible k-point sample",
        ylabel="Energy relative to PBE VBM at Γ (eV)",
        xticks=[1, 2, 3, 4],
        xticklabels=["Γ", "k₂", "k₃", "k₄"],
        title="Sampled bands 2–8",
        ylim=(-6, 5),
    )
    other.legend()
    other.grid(alpha=0.2)
    fig.savefig("si-gw-levels.png", dpi=220)


if __name__ == "__main__":
    main()
