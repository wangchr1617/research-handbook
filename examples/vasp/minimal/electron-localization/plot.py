"""用法：python3 plot.py；读取 Multiwfn elf.cub，在分数坐标 c≈0.125 处绘制切面。"""

from pathlib import Path

import matplotlib
from ase.io.cube import read_cube

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from mpl_toolkits.axes_grid1 import make_axes_locatable

FRACTION_C = 0.125  # 沿第三晶格向量的分数坐标；选最近的实际网格层，不插值。


def main():
    with Path("elf.cub").open() as stream:
        cube = read_cube(stream)
    data, cell = cube["data"], np.asarray(cube["atoms"].cell)
    index = round(FRACTION_C * data.shape[2]) % data.shape[2]
    fraction = index / data.shape[2]
    # 在 a-b 平面内建立正交坐标，保留晶格夹角，不把斜晶胞画成正方形。
    u = cell[0] / np.linalg.norm(cell[0])
    v = cell[1] - np.dot(cell[1], u) * u
    v = v / np.linalg.norm(v)
    fa, fb = np.meshgrid(
        np.arange(data.shape[0] + 1) / data.shape[0],
        np.arange(data.shape[1] + 1) / data.shape[1],
        indexing="ij",
    )
    x = fa * np.dot(cell[0], u) + fb * np.dot(cell[1], u)
    y = fa * np.dot(cell[0], v) + fb * np.dot(cell[1], v)
    fig, ax = plt.subplots(figsize=(5.8, 4.6), constrained_layout=True)
    image = ax.pcolormesh(
        x, y, data[:, :, index], shading="flat", cmap="viridis", vmin=0, vmax=1
    )
    ax.set_aspect("equal")
    ax.set(
        xlabel=r"In-plane $u$ ($\AA$)",
        ylabel=r"In-plane $v$ ($\AA$)",
        title=f"Si | ELF slice at fractional c = {fraction:.3f}",
    )
    divider = make_axes_locatable(ax)
    colorbar_axes = divider.append_axes("right", size="4%", pad=0.12)
    fig.colorbar(image, cax=colorbar_axes, label="ELF (dimensionless)")
    fig.savefig("si-elf.png", dpi=240, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print("已生成 si-elf.png")


if __name__ == "__main__":
    main()
