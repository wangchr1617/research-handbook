"""用法：python3 plot.py；按每个 H 原子归一化的电子吸附能。"""

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt


def main():
    d = json.loads(Path("adsorption-results.json").read_text())
    values = [d["adsorption_total_eV"]["half"], d["adsorption_total_eV"]["full"] / 2]
    fig, ax = plt.subplots(figsize=(5, 3.8), layout="constrained")
    ax.bar(["0.5 ML", "1 ML"], values, width=0.55)
    ax.axhline(0, color=".5")
    ax.set(
        ylabel="Electronic adsorption energy (eV / H)",
        title="H/Al(111) | H₂ reference, fixed Al substrate",
    )
    fig.savefig("al-h-adsorption.png", dpi=220)


if __name__ == "__main__":
    main()
