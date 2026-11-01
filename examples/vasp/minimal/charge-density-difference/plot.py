"""用法：python3 plot.py；绘制包含 Na、Cl 的实际网格切面，不做插值。"""

from pathlib import Path

import matplotlib
from ase.io.cube import read_cube
from ase.units import Bohr

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from mpl_toolkits.axes_grid1 import make_axes_locatable


def main():
    with Path("cdd.cub").open() as stream:
        cube = read_cube(stream)
    data = cube["data"] / Bohr**3  # e/Bohr³ → e/Å³。
    cell = np.asarray(cube["atoms"].cell)
    if len(set(data.shape)) != 1:
        raise SystemExit("本切面脚本要求三个方向的网格点数相同")
    n = data.shape[0]
    # 分数坐标 (s,t,t)，平面由 a 与 b+c 张成，包含 Na 与 Cl。
    plane = data[:, np.arange(n), np.arange(n)]
    vectors = np.array([cell[0], cell[1] + cell[2]])
    u = vectors[0] / np.linalg.norm(vectors[0])
    v = vectors[1] - np.dot(vectors[1], u) * u
    v /= np.linalg.norm(v)
    s, t = np.meshgrid(np.arange(n + 1) / n, np.arange(n + 1) / n, indexing="ij")
    x = s * np.dot(vectors[0], u) + t * np.dot(vectors[1], u)
    y = s * np.dot(vectors[0], v) + t * np.dot(vectors[1], v)
    limit = np.abs(plane).max()
    fig, ax = plt.subplots(figsize=(6.4, 4.8), constrained_layout=True)
    im = ax.pcolormesh(
        x, y, plane, cmap="RdBu_r", vmin=-limit, vmax=limit, shading="flat"
    )
    point = 0.5 * (vectors[0] + vectors[1])
    ax.plot(
        np.dot(point, u),
        np.dot(point, v),
        "o",
        markersize=6,
        markerfacecolor="none",
        markeredgecolor="black",
    )
    ax.annotate(
        "Cl",
        (np.dot(point, u), np.dot(point, v)),
        xytext=(6, 6),
        textcoords="offset points",
    )
    ax.annotate("Na", (0, 0), xytext=(3, 5), textcoords="offset points")
    ax.set_aspect("equal")
    ax.set(
        xlabel=r"In-plane $u$ ($\AA$)",
        ylabel=r"In-plane $v$ ($\AA$)",
        title=r"NaCl | $\Delta\rho$ in plane $(s,t,t)$",
    )
    divider = make_axes_locatable(ax)
    cax = divider.append_axes("right", size="4%", pad=0.12)
    fig.colorbar(im, cax=cax, label=r"$\Delta\rho$ (e/$\AA^3$)")
    fig.savefig("nacl-cdd.png", dpi=240, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print("已生成 nacl-cdd.png")


if __name__ == "__main__":
    main()
