"""用法：python3 plot.py；将 VASPKIT 的 BAND.dat、KLABELS 绘制成能带图。"""

import argparse
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


def arguments(default_output):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-dir", type=Path, default=Path("."))
    parser.add_argument("--output", type=Path, default=Path(default_output))
    return parser.parse_args()


def save(fig, output):
    output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output, dpi=240, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"已生成 {output}")


ENERGY_WINDOW = (-5, 6)  # 相对 SCF 费米能的绘图范围，单位 eV。


def main():
    args = arguments("si-bands.png")
    bands = []
    for line in (args.input_dir / "BAND.dat").read_text().splitlines():
        if line.startswith("# Band-Index"):
            bands.append([])
        elif line.strip() and not line.lstrip().startswith("#") and bands:
            bands[-1].append([float(value) for value in line.split()[:2]])
    if not bands or any(not band for band in bands):
        raise SystemExit("BAND.dat 中没有完整能带")
    labels, ticks = [], []
    for line in (args.input_dir / "KLABELS").read_text().splitlines():
        fields = line.split()
        if len(fields) != 2:
            continue
        try:
            tick = float(fields[1])
        except ValueError:
            continue
        labels.append(r"$\Gamma$" if fields[0] in ("G", "GAMMA") else fields[0])
        ticks.append(tick)
    if len(ticks) < 2:
        raise SystemExit("KLABELS 缺少路径端点")
    fig, ax = plt.subplots(figsize=(5.8, 4.3), constrained_layout=True)
    for band in bands:
        data = np.asarray(band)
        if not np.isfinite(data).all():
            raise SystemExit("能带数据含非有限值")
        ax.plot(data[:, 0], data[:, 1], color="#24618c", linewidth=1.0)
    for tick in ticks:
        ax.axvline(tick, color="0.85", linewidth=0.7)
    ax.axhline(0, color="0.35", linestyle="--", linewidth=0.8)
    ax.set(
        xlim=(ticks[0], ticks[-1]),
        ylim=ENERGY_WINDOW,
        ylabel=r"$E-E_F$ (eV)",
        title="Si | PBE band structure",
    )
    ax.set_xticks(ticks, labels)
    save(fig, args.output)


if __name__ == "__main__":
    main()
