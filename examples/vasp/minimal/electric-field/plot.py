"""用法：python3 plot.py；绘制实际正负场能量和 z 向偶极响应。"""

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt


def main():
    d = json.loads(Path("field-results.json").read_text())
    stages = ["minus", "zero", "plus"]
    fields = [d[s]["EFIELD_eV_A"] for s in stages]
    fig, axes = plt.subplots(1, 2, figsize=(8, 3.5), layout="constrained")
    axes[0].plot(
        fields,
        [(d[s]["energy_eV"] - d["zero"]["energy_eV"]) * 1000 for s in stages],
        "o-",
    )
    axes[0].set(ylabel="E − E(0) (meV)")
    axes[1].plot(fields, [d[s]["dipole_eA"][2] for s in stages], "o-")
    axes[1].set(ylabel="VASP dipole z (e Å)")
    for ax in axes:
        ax.set_xlabel("EFIELD (eV/Å)")
        ax.grid(alpha=0.2)
    fig.suptitle("H₂ | fixed-geometry field response")
    fig.savefig("h2-field.png", dpi=220)


if __name__ == "__main__":
    main()
