"""绘制展开声子谱。

用法：python plot_upho.py
运行前按下方变量设置输入、输出和计算参数。
"""

#!/usr/bin/env python
import matplotlib.pyplot as plt
import numpy as np


def main():
    distances, frequencies, sfs = np.loadtxt(
        "sf_SR.dat", usecols=(0, 1, 2), unpack=True
    )
    n2 = len(np.unique(frequencies))
    distances = distances.reshape((-1, n2))
    frequencies = frequencies.reshape((-1, n2))
    sfs = sfs.reshape((-1, n2))

    fig, ax = plt.subplots()
    ax.pcolormesh(distances, frequencies, sfs, rasterized=True)
    fig.savefig("sf.svg")


if __name__ == "__main__":
    main()
