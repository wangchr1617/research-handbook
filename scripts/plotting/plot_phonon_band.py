"""绘制 phonopy band.dat 声子能带（依赖 NumPy、Matplotlib）。

用法：python plot_phonon_band.py band.dat -o phon.png --labels G X M G
第二行 '# End points:' 后为路径端点坐标；空行分隔各条能带，频率默认 THz。
"""

import argparse
from pathlib import Path


def load_bands(path):
    lines = path.read_text().splitlines()
    if len(lines) < 3:
        raise ValueError("能带文件不完整")
    endpoints = [float(value) for value in lines[1].split()[3:]]
    if not endpoints:
        raise ValueError("第二行缺少路径端点")
    bands, current = [], []
    for line in lines[2:]:
        fields = line.split()
        if not fields:
            if current:
                bands.append(current)
                current = []
        elif not fields[0].startswith("#"):
            current.append([float(fields[0]), float(fields[1])])
    if current:
        bands.append(current)
    if not bands:
        raise ValueError("没有能带数据")
    return endpoints, bands


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("-o", "--output", type=Path, default=Path("phon.png"))
    parser.add_argument("--labels", nargs="+", help="路径端点的显示标签")
    parser.add_argument("--frequency-unit", default="THz")
    args = parser.parse_args()
    try:
        endpoints, bands = load_bands(args.input)
    except (ValueError, OSError, IndexError) as error:
        parser.exit(1, f"错误：{error}\n")
    if args.labels and len(args.labels) != len(endpoints):
        parser.error("标签数与路径端点数不一致")
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np

    fig, ax = plt.subplots(figsize=(5, 4))
    for band in bands:
        data = np.array(band)
        ax.plot(data[:, 0], data[:, 1], color="red", linewidth=0.8)
    ax.set(
        xlim=(min(endpoints), max(endpoints)),
        ylabel=f"Frequency / {args.frequency_unit}",
    )
    ax.set_xticks(endpoints)
    if args.labels:
        ax.set_xticklabels(args.labels)
    for point in endpoints:
        ax.axvline(point, color="0.5", linestyle="--", linewidth=0.8)
    ax.axhline(0, color="0.5", linestyle="--", linewidth=0.8)
    fig.tight_layout()
    fig.savefig(args.output, dpi=300)
    plt.close(fig)


if __name__ == "__main__":
    main()
