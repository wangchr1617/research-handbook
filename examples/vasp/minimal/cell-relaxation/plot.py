"""用法：python3 plot.py；从 vasprun.xml 绘制优化能量和受力或体积。"""

import xml.etree.ElementTree as ET

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

CELL_OPTIMIZATION = True  # 晶胞优化画体积；固定晶胞优化画最大原子受力。


def main():
    calculations = ET.parse("vasprun.xml").getroot().findall("calculation")
    energies, forces, volumes = [], [], []
    for calculation in calculations:
        energies.append(float(calculation.find("energy/i[@name='e_0_energy']").text))
        vectors = np.array(
            [
                [float(value) for value in row.text.split()]
                for row in calculation.findall("varray[@name='forces']/v")
            ]
        )
        forces.append(np.linalg.norm(vectors, axis=1).max())
        volumes.append(
            float(calculation.find("structure/crystal/i[@name='volume']").text)
        )
    if not energies or not np.isfinite([energies, forces, volumes]).all():
        raise SystemExit("优化数据缺失或含非有限值")
    steps = np.arange(1, len(energies) + 1)
    fig, axes = plt.subplots(
        2, 1, figsize=(5.8, 5.8), sharex=True, constrained_layout=True
    )
    axes[0].plot(
        steps,
        (np.array(energies) - energies[0]) * 1000,
        "o-",
        color="#24618c",
        markersize=4,
    )
    axes[0].set(ylabel="Energy change (meV/cell)", title="Si | cell optimization")
    if CELL_OPTIMIZATION:
        axes[1].plot(steps, volumes, "o-", color="#a54828", markersize=4)
        axes[1].set_ylabel(r"Volume ($\AA^3$/cell)")
    else:
        axes[1].plot(steps, forces, "o-", color="#a54828", markersize=4)
        axes[1].axhline(0.015, color="0.4", linestyle="--", label=r"0.015 eV/$\AA$")
        axes[1].set_yscale("log")
        axes[1].set_ylabel(r"Maximum force (eV/$\AA$)")
        axes[1].legend(frameon=False)
    axes[1].set_xlabel("Ionic step")
    axes[1].set_xticks(steps)
    fig.savefig(
        "si-cell-relaxation.png", dpi=240, bbox_inches="tight", facecolor="white"
    )
    plt.close(fig)
    print("已生成 si-cell-relaxation.png")


if __name__ == "__main__":
    main()
