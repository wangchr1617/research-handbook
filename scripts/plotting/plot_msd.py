"""绘制单文件分量或多文件总 MSD（依赖 NumPy、Matplotlib）。

用法：python plot_msd.py msd.out --columns 1 2 3 --time-unit ps
      python plot_msd.py MSD_1.dat MSD_2.dat --skiprows 1 --columns 4 --time-unit fs
列号从零开始，第一列是时间；不猜测时间单位，默认 ps，可用 --time-scale 换算。
"""

import argparse
from pathlib import Path


def load_msd_data(path, skiprows=0):
    import numpy as np

    data = np.loadtxt(path, skiprows=skiprows, ndmin=2)
    if len(data) < 1 or data.shape[1] < 2 or not np.isfinite(data).all():
        raise ValueError(f"{path} 数据为空、列不足或含非有限数")
    return data


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("files", nargs="+", type=Path)
    parser.add_argument("--skiprows", type=int, default=0, help="需跳过的表头行数")
    parser.add_argument(
        "--columns", nargs="+", type=int, default=[1, 2, 3], help="零起始 MSD 列号"
    )
    parser.add_argument("--time-scale", type=float, default=1.0, help="时间列乘数")
    parser.add_argument("--time-unit", default="ps")
    parser.add_argument("-o", "--output", type=Path, default=Path("msd.png"))
    args = parser.parse_args()
    if args.skiprows < 0 or min(args.columns) < 1 or args.time_scale <= 0:
        parser.error("行数、列号或时间换算系数无效")
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(6, 4))
    for path in args.files:
        data = load_msd_data(path, args.skiprows)
        if max(args.columns) >= data.shape[1]:
            parser.error(f"{path} 没有要求的列")
        for column in args.columns:
            ax.plot(
                data[:, 0] * args.time_scale,
                data[:, column],
                label=f"{path.stem}: col {column}",
            )
    ax.set(xlabel=f"Time / {args.time_unit}", ylabel="MSD / Å²")
    ax.legend()
    fig.tight_layout()
    fig.savefig(args.output, dpi=300)
    plt.close(fig)


if __name__ == "__main__":
    main()
