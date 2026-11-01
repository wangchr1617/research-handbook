"""用法：python3 plot.py；从实际输出绘制优化中的能量评估轨迹。"""

import re
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from ase.units import Hartree


def main():
    text = Path("cp2k.out").read_text(errors="replace")
    energies = np.array(
        [
            float(v)
            for v in re.findall(
                r"ENERGY\| Total FORCE_EVAL.*?energy.*?\s+([-+0-9.Ee]+)\s*$",
                text,
                re.MULTILINE,
            )
        ]
    )
    if energies.size < 2 or not np.isfinite(energies).all():
        raise SystemExit("缺少有效能量轨迹")
    fig, ax = plt.subplots(figsize=(6, 3.8), layout="constrained")
    ax.plot(np.arange(1, len(energies) + 1), (energies - energies[0]) * Hartree, "o-")
    ax.set(
        xlabel="Energy evaluation",
        ylabel="E − E(first) (eV)",
        title="CP2K | optimization energy history",
    )
    ax.grid(alpha=0.2)
    fig.savefig("optimization-energy.png", dpi=220)


if __name__ == "__main__":
    main()
