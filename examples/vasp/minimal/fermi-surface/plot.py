"""用法：python3 plot.py；用 scikit-image 等值面绘制倒易原胞内的真实费米面。"""

import itertools

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.lines import Line2D
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
from skimage.measure import marching_cubes


def main():
    data = np.load("fermi-grid.npz")
    e = data["energies"]
    n = len(e)
    fermi = float(data["fermi"])
    basis = data["reciprocal"]
    fig = plt.figure(figsize=(6.5, 5.3), layout="constrained")
    ax = fig.add_subplot(projection="3d")
    handles = []
    for band in range(e.shape[-1]):
        if not e[:, :, :, band].min() < fermi < e[:, :, :, band].max():
            continue
        periodic = np.pad(e[:, :, :, band], ((0, 1),) * 3, mode="wrap")
        vertices, faces, _, _ = marching_cubes(
            periodic, level=fermi, spacing=(1 / n,) * 3
        )
        vertices = (vertices - 0.5) @ basis
        mesh = Poly3DCollection(
            vertices[faces],
            alpha=0.8,
            facecolor=plt.get_cmap("tab10")(band),
            edgecolor="none",
        )
        ax.add_collection3d(mesh)
        handles.append(
            Line2D(
                [0],
                [0],
                color=plt.get_cmap("tab10")(band),
                lw=5,
                label=f"Band {band + 1}",
            )
        )
    for corner in itertools.product([-0.5, 0.5], repeat=3):
        for axis in range(3):
            if corner[axis] != -0.5:
                continue
            other = list(corner)
            other[axis] = 0.5
            line = np.array([corner, other]) @ basis
            ax.plot(*line.T, color=".35", lw=0.65)
    corners = np.array(list(itertools.product([-0.5, 0.5], repeat=3))) @ basis
    ax.set(
        xlim=(corners[:, 0].min(), corners[:, 0].max()),
        ylim=(corners[:, 1].min(), corners[:, 1].max()),
        zlim=(corners[:, 2].min(), corners[:, 2].max()),
        xlabel="kx (Å⁻¹)",
        ylabel="ky (Å⁻¹)",
        zlabel="kz (Å⁻¹)",
        title="Al | reciprocal primitive cell",
    )
    ax.set_box_aspect(np.ptp(corners, axis=0))
    ax.view_init(elev=24, azim=38)
    ax.legend(handles=handles, loc="upper left")
    fig.savefig("al-fermi-surface.png", dpi=220)


if __name__ == "__main__":
    main()
