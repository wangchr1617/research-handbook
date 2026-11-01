"""用法：python3 plot.py；绘制 QHA 平衡体积和体膨胀系数。"""

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


def main():
    result = json.loads(Path("qha-results.json").read_text())
    temperatures = np.array(result["temperatures_K"])
    volumes = np.array(result["equilibrium_volumes_A3"])
    expansion = np.array(result["volumetric_expansion_K_inv"])
    fig, axes = plt.subplots(
        2, 1, figsize=(6, 5.6), sharex=True, constrained_layout=True
    )
    axes[0].plot(temperatures, volumes, "o-", color="#24618c")
    axes[0].set(
        ylabel=r"Volume ($\AA^3$/primitive cell)", title="Si | quasi-harmonic example"
    )
    # 第一个膨胀系数是数值微分的占位值，不作为真实导数绘出。
    axes[1].plot(temperatures[1:], expansion[1:] * 1e6, "o-", color="#a54828")
    axes[1].set(xlabel="Temperature (K)", ylabel=r"$\beta$ ($10^{-6}$ K$^{-1}$)")
    axes[1].axhline(0, color="0.5", linewidth=0.7)
    for ax in axes:
        ax.grid(alpha=0.2)
    fig.savefig("si-qha.png", dpi=240, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print("已生成 si-qha.png")


if __name__ == "__main__":
    main()
