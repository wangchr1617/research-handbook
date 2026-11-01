"""用法：python3 plot.py；将 VASPKIT 已按费米能置零的 TDOS.dat 绘制成图。"""

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


ENERGY_WINDOW = (-6, 6)  # 绘图能量范围，单位 eV；不对原始 DOS 做平滑。


def main():
    args = arguments("si-dos.png")
    data = np.loadtxt(args.input_dir / "TDOS.dat")
    if data.ndim != 2 or data.shape[1] != 2 or not np.isfinite(data).all():
        raise SystemExit("本例需要非自旋极化的两列 TDOS.dat")
    fig, ax = plt.subplots(figsize=(5.8, 4.0), constrained_layout=True)
    ax.plot(data[:, 0], data[:, 1], color="#24618c", linewidth=1.3)
    ax.fill_between(data[:, 0], data[:, 1], color="#24618c", alpha=0.12)
    ax.axvline(0, color="0.35", linestyle="--", linewidth=0.8)
    ax.set(
        xlim=ENERGY_WINDOW,
        ylim=(0, None),
        xlabel=r"$E-E_F$ (eV)",
        ylabel="DOS (states/eV/cell)",
        title="Si | PBE density of states",
    )
    save(fig, args.output)


if __name__ == "__main__":
    main()
