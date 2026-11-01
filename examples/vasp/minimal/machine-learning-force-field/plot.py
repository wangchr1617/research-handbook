"""用法：python3 plot.py；比较一个独立测试构型的 DFT 与 MLFF 力分量。"""

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


def main():
    result = json.loads(Path("mlff-results.json").read_text())
    reference = np.array(result["reference_forces_eV_A"]).ravel()
    prediction = np.array(result["predicted_forces_eV_A"]).ravel()
    limit = max(np.abs(reference).max(), np.abs(prediction).max()) * 1.08
    fig, ax = plt.subplots(figsize=(4.8, 4.6), constrained_layout=True)
    ax.plot([-limit, limit], [-limit, limit], "--", color="0.5", linewidth=1)
    ax.scatter(reference, prediction, color="#24618c", s=26)
    ax.set(
        xlabel=r"DFT force component (eV/$\AA$)",
        ylabel=r"MLFF force component (eV/$\AA$)",
        title="Si | one held-out configuration",
        xlim=(-limit, limit),
        ylim=(-limit, limit),
    )
    ax.set_aspect("equal")
    ax.grid(alpha=0.2)
    fig.savefig("si-mlff-forces.png", dpi=240, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print("已生成 si-mlff-forces.png")


if __name__ == "__main__":
    main()
