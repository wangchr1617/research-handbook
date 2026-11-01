"""用法：python3 plot.py；绘制 BSE 实际吸收相关介电虚部，不赋予实验精度。"""

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


def main():
    a = np.loadtxt("bse-dielectric.dat")
    fig, ax = plt.subplots(figsize=(6, 3.8), layout="constrained")
    ax.plot(a[:, 0], a[:, 1:4].mean(axis=1))
    ax.set(
        xlabel="Photon energy (eV)",
        ylabel="Mean Im ε (dimensionless)",
        title="Si | coarse BSE optical response",
        xlim=(0, 15),
    )
    ax.grid(alpha=0.2)
    fig.savefig("si-bse.png", dpi=220)


if __name__ == "__main__":
    main()
