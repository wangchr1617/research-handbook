"""用法：python3 plane_profile.py cdd.cub --density-unit e/bohr3。

将单场电子密度 Cube 沿网格晶面求平均、截面积分和累计电子数；支持斜晶胞。
--axis 为网格向量编号 1/2/3，--density-unit 明确输入值单位。
输出前缀默认为 cdd-plane-profile，生成数值表、图片和科学元数据。
"""

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
from ase.io.cube import read_cube
from ase.units import Bohr


def plane_profile(density, cell, axis=2):
    """density 单位 e/Å³，cell 为三个晶格向量组成的行矩阵，单位 Å。"""
    density = np.asarray(density, dtype=float)
    cell = np.asarray(cell, dtype=float)
    if density.ndim != 3 or not np.isfinite(density).all():
        raise ValueError("需要有限数值的三维单场网格")
    if cell.shape != (3, 3) or not np.isfinite(cell).all() or axis not in (0, 1, 2):
        raise ValueError("晶胞必须为有限的 3×3 行向量矩阵，axis 为 0/1/2")
    other = tuple(i for i in range(3) if i != axis)
    cross = np.cross(cell[other[0]], cell[other[1]])
    area = float(np.linalg.norm(cross))
    volume = float(abs(np.linalg.det(cell)))
    if area <= 0 or volume <= 1e-12:
        raise ValueError("晶胞面积或体积为零")
    normal = cross / area
    if normal @ cell[axis] < 0:
        normal *= -1
    height = volume / area
    step = height / density.shape[axis]
    average = density.mean(axis=other)
    local = average * area
    cumulative = np.cumsum(local) * step
    # 周期网格不重复末端点；累计和对应每层上边界，均值对应采样平面。
    sample = np.arange(len(average)) * step
    upper = sample + step
    values = np.column_stack([sample, average, local, upper, cumulative])
    metadata = {
        "plane_normal": normal.tolist(),
        "plane_area_A2": area,
        "normal_height_A": height,
        "layer_step_A": step,
        "integral_e": float(cumulative[-1]),
        "volume_integral_e": float(density.mean() * volume),
    }
    return values, metadata


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("cube", type=Path)
    parser.add_argument("--density-unit", choices=["e/bohr3", "e/angstrom3"], required=True)
    parser.add_argument("--axis", type=int, choices=[1, 2, 3], default=3)
    parser.add_argument("--output-prefix", type=Path, default=Path("cdd-plane-profile"))
    args = parser.parse_args()
    with args.cube.open() as stream:
        cube = read_cube(stream)
    if len(cube.get("datas", [cube["data"]])) != 1:
        raise SystemExit("请先导出单一物理量的 Cube，不自动选择多场或多轨道数据")
    density = cube["data"]
    if args.density_unit == "e/bohr3":
        density = density / Bohr**3
    values, metadata = plane_profile(density, cube["atoms"].cell.array, args.axis - 1)
    metadata.update(
        input_file=args.cube.name,
        input_sha256=hashlib.sha256(args.cube.read_bytes()).hexdigest(),
        script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        grid_shape=list(density.shape),
        grid_axis=args.axis,
        density_input_unit=args.density_unit,
        origin_A=cube["origin"].tolist(),
        coordinate="u measured from cube origin along the positive selected plane normal",
        columns=["sample_u_A", "plane_average_e_A3", "plane_integral_e_A", "upper_u_A", "cumulative_e"],
    )
    prefix = args.output_prefix
    np.savetxt(str(prefix) + ".dat", values, header=" ".join(metadata["columns"]))
    Path(str(prefix) + ".json").write_text(json.dumps(metadata, indent=2) + "\n")

    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, axes = plt.subplots(2, 1, figsize=(7.0, 5.4), sharex=True, constrained_layout=True)
    axes[0].plot(values[:, 0], values[:, 1], color="#2667a8", lw=1.7)
    axes[0].set_ylabel(r"Plane average ($e\,\mathrm{\AA}^{-3}$)")
    axes[1].plot(np.r_[0, values[:, 3]], np.r_[0, values[:, 4]], color="#b74b34", lw=1.7)
    axes[1].set_ylabel("Cumulative electrons")
    axes[1].set_xlabel(r"$u$ along plane normal ($\mathrm{\AA}$)")
    for ax in axes:
        ax.axhline(0, color="0.55", lw=0.7, ls="--")
        ax.grid(alpha=0.18)
    fig.savefig(str(prefix) + ".png", dpi=180)
    plt.close(fig)
    print(json.dumps(metadata, indent=2))


if __name__ == "__main__":
    main()
