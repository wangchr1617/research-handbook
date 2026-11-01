"""用法：python3 plot.py；同构型的 PBE 与 PBE0 原子受力分量对比。"""

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


def main():
    d = json.loads(Path("hybrid-results.json").read_text())
    fig, ax = plt.subplots(figsize=(6, 3.8), layout="constrained")
    x = np.arange(9)
    for name in ["pbe", "pbe0"]:
        ax.plot(x, np.array(d[name]["forces_eV_A"]).ravel(), "o-", label=name.upper())
    ax.set(
        xticks=x,
        xticklabels=[f"{atom}-{axis}" for atom in ["O", "H1", "H2"] for axis in "xyz"],
        ylabel="Force (eV/Å)",
        title="H₂O | same geometry, two functionals",
    )
    ax.legend()
    ax.grid(alpha=0.2)
    fig.savefig("water-hybrid-forces.png", dpi=220)


if __name__ == "__main__":
    main()
