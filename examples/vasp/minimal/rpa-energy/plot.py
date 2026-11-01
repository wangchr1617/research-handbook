"""用法：python3 plot.py；绘制一次 RPA 计算输出的内部截断扫描。"""

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


def main():
    a = np.loadtxt("rpa-cutoffs.dat")
    a = a[np.argsort(a[:, 0])]
    fig, ax = plt.subplots(figsize=(6, 3.8), layout="constrained")
    ax.plot(a[:, 0], a[:, 2], "o-")
    ax.set(
        xlabel="Response cutoff (eV)",
        ylabel="RPA correlation energy (eV / 2-Si cell)",
        title="Si | internal cutoff scan, fixed 24 bands",
    )
    ax.grid(alpha=0.2)
    fig.savefig("si-rpa.png", dpi=220)


if __name__ == "__main__":
    main()
