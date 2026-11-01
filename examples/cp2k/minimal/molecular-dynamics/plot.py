"""用法：python3 plot.py；绘制实际 NVT 温度及相对势能。"""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from ase.units import Hartree


def main():
    files = list(Path(".").glob("*-1.ener"))
    if len(files) != 1:
        raise SystemExit("需要唯一的 *-1.ener 文件")
    values = np.loadtxt(files[0], ndmin=2)
    if not np.isfinite(values).all():
        raise SystemExit("能量记录包含非有限数值")
    fig, axes = plt.subplots(2, 1, figsize=(6, 5.2), sharex=True, layout="constrained")
    axes[0].plot(values[:, 1], values[:, 3], "o-")
    axes[0].set(ylabel="Temperature (K)", title="H₂O | short NVT trajectory")
    axes[1].plot(values[:, 1], (values[:, 4] - values[0, 4]) * Hartree * 1000, "o-")
    axes[1].set(xlabel="Time (fs)", ylabel="ΔE(potential) (meV)")
    for ax in axes:
        ax.grid(alpha=0.2)
    fig.savefig("water-aimd.png", dpi=220)


if __name__ == "__main__":
    main()
