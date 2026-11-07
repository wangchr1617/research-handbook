"""计算 NEP 预测与参考值的分量 RMSE（依赖 NumPy）。

用法：python calculate_rmse.py [--directory 结果目录]
能量取前 2 列，力取前 3/后 3 列，virial 取前 6/后 6 列。
能量和 virial 输入须已为 eV/atom，力为 eV/Å；输出乘 1000 转为 meV。
不自动除以原子数，不将 virial 当作压力或应力。
"""

import argparse
from pathlib import Path

import numpy as np


def paired_rmse(file_path, components):
    """按所有行、所有分量求平方差均值；允许输入附带额外列。"""
    data = np.loadtxt(file_path, ndmin=2)
    if data.shape[0] == 0 or data.shape[1] < 2 * components:
        raise ValueError(f"{file_path}：需要非空数据和至少 {2 * components} 列")
    selected = data[:, : 2 * components]
    if not np.isfinite(selected).all():
        raise ValueError(f"{file_path}：参与计算的数据含 NaN 或无穷大")
    # 缩放后求均方根，避免有效但较大的分量差在平方时溢出。
    with np.errstate(over="raise", invalid="raise"):
        try:
            difference = selected[:, :components] - selected[:, components:]
            scale = np.max(np.abs(difference))
            result = (
                0.0
                if scale == 0
                else scale * np.sqrt(np.mean((difference / scale) ** 2))
            )
            result *= 1000
        except FloatingPointError as error:
            raise ValueError(f"{file_path}：差值或单位换算超出浮点范围") from error
    if not np.isfinite(result):
        raise ValueError(f"{file_path}：RMSE 超出浮点范围")
    return float(result)


def calculate_rmse_energy(file_path):
    """返回 meV/atom；输入两列均为 eV/atom。"""
    return paired_rmse(file_path, 1)


def calculate_rmse_force(file_path):
    """返回 meV/Å；输入前后三列分别为预测和参考力分量。"""
    return paired_rmse(file_path, 3)


def calculate_rmse_virial(file_path):
    """返回 meV/atom；输入前后六列分别为预测和参考 virial。"""
    return paired_rmse(file_path, 6)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--directory", type=Path, default=Path("."))
    parser.add_argument("--energy", type=Path, default=Path("energy_train.out"))
    parser.add_argument("--force", type=Path, default=Path("force_train.out"))
    parser.add_argument("--virial", type=Path, default=Path("virial_train.out"))
    args = parser.parse_args()
    try:
        results = [
            ("Energy", calculate_rmse_energy(args.directory / args.energy), "meV/atom"),
            ("Force", calculate_rmse_force(args.directory / args.force), "meV/Å"),
            ("Virial", calculate_rmse_virial(args.directory / args.virial), "meV/atom"),
        ]
    except (OSError, ValueError) as error:
        parser.exit(1, f"错误：{error}\n")
    for label, value, unit in results:
        print(f"{label} RMSE: {value:.2f} {unit}")


if __name__ == "__main__":
    main()
