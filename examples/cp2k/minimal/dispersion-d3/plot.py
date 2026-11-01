"""用法：python3 plot.py；以 PBE 能量为参考显示实际 D3(BJ) 修正。"""

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt


def main():
    d = json.loads(Path("dispersion-results.json").read_text())
    value = d["total_energy_difference_eV"] * 1000
    fig, ax = plt.subplots(figsize=(5, 3.8), layout="constrained")
    ax.bar(["PBE", "PBE-D3(BJ)"], [0, value], width=0.55)
    ax.axhline(0, color=".5")
    ax.set(ylabel="E − E(PBE) (meV)", title="Water dimer | same nonperiodic geometry")
    fig.savefig("water-d3.png", dpi=220)


if __name__ == "__main__":
    main()
