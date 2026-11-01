"""用法：python3 plot.py；从实际 XML 绘制晶格常数优化轨迹。"""

import xml.etree.ElementTree as ET

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from ase.io import read


def main():
    cells = [read("POSCAR").cell.array] + [
        np.array(
            [
                [float(v) for v in row.text.split()]
                for row in c.findall("structure/crystal/varray[@name='basis']/v")
            ]
        )
        for c in ET.parse("vasprun.xml").getroot().findall("calculation")
    ]
    lengths = np.linalg.norm(cells, axis=2)
    fig, ax = plt.subplots(figsize=(6, 3.8), layout="constrained")
    for i, label in enumerate(["a", "b", "c (fixed)"]):
        ax.plot(
            range(len(cells)), lengths[:, i], marker=["o", "x", "s"][i], label=label
        )
    ax.set(
        xlabel="Ionic step (0: input)",
        ylabel="Lattice constant (Å)",
        title="Si | constrained cell relaxation",
    )
    ax.legend()
    ax.grid(alpha=0.2)
    fig.savefig("si-fixed-cell.png", dpi=220)


if __name__ == "__main__":
    main()
