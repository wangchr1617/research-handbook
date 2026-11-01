"""用法：python3 plot.py；展示三个内部正常模式频率，不赋予光谱强度。"""

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt


def main():
    frequencies = json.loads(Path("results.json").read_text())["frequencies_cm-1"]
    fig, ax = plt.subplots(figsize=(6, 3.8), layout="constrained")
    ax.scatter([1, 2, 3], frequencies, s=55)
    for i, f in enumerate(frequencies, 1):
        ax.annotate(
            f"{f:.1f}", (i, f), xytext=(0, 9), textcoords="offset points", ha="center"
        )
    ax.set(
        xlabel="Internal normal mode",
        ylabel="Frequency (cm⁻¹)",
        title="H₂O | harmonic vibrational frequencies",
        xticks=[1, 2, 3],
        xlim=(0.5, 3.5),
        ylim=(0, 4300),
    )
    ax.grid(alpha=0.2)
    fig.savefig("water-frequencies.png", dpi=220)


if __name__ == "__main__":
    main()
