"""用法：python3 plot.py；绘制 NaCl 两组网格的 Bader 净原子电荷。"""

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


def main():
    results = json.loads(Path("bader-results.json").read_text())["results"]
    fig, ax = plt.subplots(figsize=(5.8, 4.0), constrained_layout=True)
    positions = np.arange(2)
    for index, result in enumerate(results):
        ax.bar(
            positions + (index - 0.5) * 0.3,
            result["net_charge_e"],
            width=0.28,
            color=["#24618c", "#a54828"][index],
            label=f"{result['grid']} cubed grid",
        )
    ax.axhline(0, color="0.3", linewidth=0.8)
    ax.set_xticks(positions, ["Na", "Cl"])
    ax.set(ylabel="Bader net charge (e)", title="NaCl | grid comparison")
    ax.legend(frameon=False)
    fig.savefig("nacl-bader.png", dpi=240, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print("已生成 nacl-bader.png")


if __name__ == "__main__":
    main()
