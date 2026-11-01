"""用法：python3 plot.py；绘制 VASPKIT 导出的弹性矩阵（GPa）。"""

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


def main():
    data = json.loads(Path("elastic-results.json").read_text())
    stiffness = np.array(data["stiffness_GPa"])
    fig, ax = plt.subplots(figsize=(5.4, 4.4), constrained_layout=True)
    im = ax.imshow(stiffness, cmap="Blues", vmin=0, vmax=stiffness.max())
    labels = ["xx", "yy", "zz", "yz", "xz", "xy"]
    ax.set_xticks(range(6), labels)
    ax.set_yticks(range(6), labels)
    ax.set_title("Si | relaxed-ion elastic tensor")
    for i in range(6):
        for j in range(6):
            ax.text(
                j,
                i,
                f"{stiffness[i, j]:.1f}",
                ha="center",
                va="center",
                color="white" if stiffness[i, j] > 0.6 * stiffness.max() else "black",
            )
    fig.colorbar(im, ax=ax, label="Stiffness (GPa)")
    fig.savefig("si-elastic.png", dpi=240, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print("已生成 si-elastic.png")


if __name__ == "__main__":
    main()
