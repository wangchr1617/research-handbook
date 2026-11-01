"""用法：python3 plot.py；读取 Phonopy 热力学输出，绘制定容热容。"""

import argparse
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import yaml


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


GAS_CONSTANT = 8.314462618  # 摩尔气体常数，单位 J/(mol K)。


def main():
    args = arguments("si-heat-capacity.png")
    data = yaml.safe_load((args.input_dir / "thermal_properties.yaml").read_text())
    temperature = np.array([row["temperature"] for row in data["thermal_properties"]])
    cv = np.array([row["heat_capacity"] for row in data["thermal_properties"]])
    if not np.isfinite(cv).all():
        raise SystemExit("热容数据含非有限值")
    # 保留 Phonopy 每摩尔原胞的归一化，不能误标为每摩尔 Si 原子。
    limit = 3 * data["natom"] * GAS_CONSTANT
    fig, ax = plt.subplots(figsize=(5.8, 4.0), constrained_layout=True)
    ax.plot(
        temperature,
        cv,
        "o-",
        color="#24618c",
        markersize=4,
        linewidth=1.3,
        label=r"Harmonic $C_V$",
    )
    ax.axhline(limit, color="0.4", linestyle="--", linewidth=0.9, label=r"$3nR$ limit")
    ax.set(
        xlim=(temperature.min(), temperature.max()),
        ylim=(0, limit * 1.08),
        xlabel="Temperature (K)",
        ylabel=r"$C_V$ (J mol$^{-1}$ K$^{-1}$)",
        title=f"Si | harmonic heat capacity ({data['natom']} atoms/cell)",
    )
    ax.legend(frameon=False)
    save(fig, args.output)


if __name__ == "__main__":
    main()
