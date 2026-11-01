"""用法：python3 plot.py；绘制 VASPKIT 输出的硅介电函数与吸收谱。"""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ENERGY_MAX_EV = 12  # 图示光子能量上限；不改变计算数据。


def main():
    real = np.loadtxt("REAL.in")
    imag = np.loadtxt("IMAG.in")
    absorption = np.loadtxt("ABSORPTION.dat", comments="#")
    for data in [real, imag, absorption]:
        if data.ndim != 2 or data.shape[1] < 4 or not np.isfinite(data).all():
            raise SystemExit("光学数据列数不完整或包含非有限值")
    if real.shape != imag.shape or not np.allclose(real[:, 0], imag[:, 0]):
        raise SystemExit("介电函数实部和虚部的能量网格不一致")
    fig, axes = plt.subplots(
        2, 1, figsize=(6, 5.5), sharex=True, constrained_layout=True
    )
    axes[0].plot(real[:, 0], real[:, 1:4].mean(axis=1), label=r"$\epsilon_1$")
    axes[0].plot(imag[:, 0], imag[:, 1:4].mean(axis=1), label=r"$\epsilon_2$")
    axes[0].set(ylabel="Dielectric function", title="Si | coarse-grid optical example")
    axes[0].axhline(0, color="0.5", linewidth=0.7)
    axes[0].legend(frameon=False)
    axes[1].plot(
        absorption[:, 0], absorption[:, 1:4].mean(axis=1) / 1e5, color="#24618c"
    )
    axes[1].set(
        xlabel="Photon energy (eV)",
        ylabel=r"Absorption ($10^5$ cm$^{-1}$)",
        xlim=(0, ENERGY_MAX_EV),
    )
    for ax in axes:
        ax.grid(alpha=0.2)
    fig.savefig(Path("si-optics.png"), dpi=240, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print("已生成 si-optics.png")


if __name__ == "__main__":
    main()
