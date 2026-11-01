"""用法：python3 plot.py；绘制 phono3py 的 RTA 晶格热导率。"""

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


def main():
    result = json.loads(Path("thermal-conductivity-results.json").read_text())
    tensor = np.asarray(result["kappa_W_mK"])
    fig, ax = plt.subplots(figsize=(5.8, 4.2), constrained_layout=True)
    ax.plot(result["temperatures_K"], tensor[:, :3].mean(axis=1), "o-", color="#24618c")
    ax.set(
        xlabel="Temperature (K)",
        ylabel=r"$\kappa_l$ (W m$^{-1}$ K$^{-1}$)",
        title="Si | coarse-grid RTA example",
    )
    ax.grid(alpha=0.2)
    fig.savefig(
        "si-lattice-thermal-conductivity.png",
        dpi=240,
        bbox_inches="tight",
        facecolor="white",
    )
    plt.close(fig)
    print("已生成 si-lattice-thermal-conductivity.png")


if __name__ == "__main__":
    main()
