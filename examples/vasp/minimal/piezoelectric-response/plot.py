"""用法：python3 plot.py；展示 e14 的电子/离子抵消和总张量。"""

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


def main():
    d = json.loads(Path("piezo-results.json").read_text())
    total = np.array(d["total_C_m2"])
    fig, axes = plt.subplots(1, 2, figsize=(9, 3.8), layout="constrained")
    values = [
        np.array(d[k])[0, 3] for k in ["electronic_C_m2", "ionic_C_m2", "total_C_m2"]
    ]
    axes[0].bar(
        ["Electronic", "Ionic", "Total"],
        values,
        color=["tab:blue", "tab:orange", "tab:green"],
    )
    axes[0].axhline(0, color=".5")
    axes[0].set(ylabel="e14 (C/m²)", title="ZnS | ionic contribution matters")
    image = axes[1].imshow(
        total,
        cmap="RdBu_r",
        vmin=-abs(total).max(),
        vmax=abs(total).max(),
        aspect="auto",
    )
    axes[1].set(
        xticks=range(6),
        xticklabels=d["voigt_order"],
        yticks=range(3),
        yticklabels=["Px", "Py", "Pz"],
        title="Total piezoelectric e tensor",
    )
    fig.colorbar(image, ax=axes[1], label="C/m²")
    fig.savefig("zns-piezo.png", dpi=220)


if __name__ == "__main__":
    main()
