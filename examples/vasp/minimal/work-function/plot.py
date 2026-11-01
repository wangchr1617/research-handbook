"""用法：python3 plot.py；实际平面平均静电势、费米能和真空平台。"""

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


def main():
    d = json.loads(Path("work-function-results.json").read_text())
    a = np.loadtxt("potential-profile.dat")
    fig, ax = plt.subplots(figsize=(6, 4), layout="constrained")
    ax.plot(a[:, 0], a[:, 1], label="Planar-averaged electrostatic potential")
    ax.axhline(d["fermi_eV"], ls="--", color="tab:orange", label="Fermi energy")
    ax.axhline(np.mean(d["vacuum_levels_eV"]), ls=":", color="k", label="Vacuum level")
    ax.set(
        xlabel="z (Å)", ylabel="Energy (eV)", title="Al(111) | four-layer ideal slab"
    )
    ax.legend(fontsize=8)
    ax.grid(alpha=0.2)
    fig.savefig("al-work-function.png", dpi=220)


if __name__ == "__main__":
    main()
