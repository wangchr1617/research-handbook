"""用法：python3 plot.py；将 VASPKIT EOS 的数据点与拟合曲线绘制成图。"""

import argparse
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("si-eos.png"))
    args = parser.parse_args()
    data = np.loadtxt("ENERGY_VOLUME_DFT.dat")
    fit = np.loadtxt("ENERGY_VOLUME_FIT.dat")
    parameters = json.loads(Path("results.json").read_text())
    if not (np.isfinite(data).all() and np.isfinite(fit).all()):
        raise SystemExit("EOS 数据含非有限值")
    # VASPKIT 两份表均按每原子归一化；日志中的 E0、V0 则对应两原子胞。
    energy_zero = parameters["energy_eV_cell"] / 2
    equilibrium_volume = parameters["volume_A3_cell"] / 2
    fig, ax = plt.subplots(figsize=(5.8, 4.0), constrained_layout=True)
    ax.plot(
        fit[:, 0],
        (fit[:, 1] - energy_zero) * 1000,
        color="#24618c",
        linewidth=1.4,
        label="Birch-Murnaghan (3rd order)",
    )
    ax.scatter(
        data[:, 0],
        (data[:, 1] - energy_zero) * 1000,
        s=30,
        color="#a54828",
        zorder=3,
        label="DFT points",
    )
    ax.axvline(equilibrium_volume, color="0.5", linestyle="--", linewidth=0.8)
    ax.set(
        xlabel=r"Volume ($\AA^3$/atom)",
        ylabel=r"$E-E_0$ (meV/atom)",
        title="Si | equation of state",
    )
    ax.legend(frameon=True, facecolor="white", edgecolor="white", framealpha=1)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(args.output, dpi=240, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"已生成 {args.output}")


if __name__ == "__main__":
    main()
