"""用法：python3 plot.py；对比相同粗网格上实际求得的带隙。"""

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt


def main():
    d = json.loads(Path("hse-results.json").read_text())
    v = [d[s]["sampled_gap_eV"] for s in ["pbe", "hse06"]]
    fig, ax = plt.subplots(figsize=(5, 3.8), layout="constrained")
    ax.bar(["PBE", "HSE06"], v, color=["tab:blue", "tab:orange"], width=0.55)
    for i, g in enumerate(v):
        ax.text(i, g + 0.03, f"{g:.3f}", ha="center")
    ax.set(
        ylabel="Sampled gap (eV)",
        title="Si | same 3×3×3 k mesh",
        ylim=(0, max(v) * 1.22),
    )
    fig.savefig("si-hse-gap.png", dpi=220)


if __name__ == "__main__":
    main()
