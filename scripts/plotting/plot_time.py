"""绘制截断能与耗时关系（依赖 NumPy、Matplotlib）。

用法：python plot_time.py timing.csv timing.png
CSV 前两列分别为 ENCUT/eV、Time/s；--skiprows 可跳过表头。
"""

import argparse
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--skiprows", type=int, default=0)
    args = parser.parse_args()
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np

    data = np.loadtxt(
        args.input, delimiter=",", usecols=(0, 1), ndmin=2, skiprows=args.skiprows
    )
    if not len(data) or not np.isfinite(data).all():
        parser.error("输入为空或含无效数值")
    fig, ax = plt.subplots(figsize=(5, 4))
    ax.plot(data[:, 0], data[:, 1], "rs-")
    ax.set(xlabel="ENCUT / eV", ylabel="Time / s")
    fig.tight_layout()
    fig.savefig(args.output, dpi=300)
    plt.close(fig)


if __name__ == "__main__":
    main()
