"""由实际 CP2K 水分子正常模式画位移箭头；振幅是显示参数。"""

import argparse
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    data = json.loads(args.data.read_text())
    xyz = np.array(data["coordinates_angstrom"])
    xyz -= xyz[0]
    vectors = np.array(data["display_displacements_angstrom"])
    fig, axes = plt.subplots(1, 3, figsize=(10.2, 3.4), layout="constrained")
    for n, (ax, v, freq) in enumerate(zip(axes, vectors, data["frequencies_cm_minus1"]), 1):
        for j in [1, 2]:
            ax.plot(xyz[[0, j], 0], xyz[[0, j], 1], color="0.5", lw=2)
        ax.scatter(xyz[:, 0], xyz[:, 1], s=[140, 70, 70], c=["#cc3344", "#dddddd", "#dddddd"], edgecolors="black", zorder=3)
        ax.quiver(xyz[:, 0], xyz[:, 1], v[:, 0], v[:, 1], angles="xy", scale_units="xy", scale=1,
                  color="#2266aa", width=0.018, zorder=4)
        ax.set(title=f"Mode {n}: {freq:.1f} cm$^{{-1}}$", xlabel="x relative to O (Angstrom)",
               ylabel="y relative to O (Angstrom)", xlim=(-1.1, 1.1), ylim=(-.3, 1.1), aspect="equal")
        ax.grid(alpha=.15)
    fig.suptitle("CP2K PBE/DZVP-MOLOPT-SR-GTH water modes\nMaximum display displacement = 0.15 Angstrom; no IR/Raman intensity assigned", fontsize=11)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(args.output, dpi=180, metadata={"Software": "matplotlib"})
    plt.close(fig)


if __name__ == "__main__":
    main()
