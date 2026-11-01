"""绘制 NEB 能量曲线。

用法：python plot_neb.py
"""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

plt.rcParams["xtick.direction"] = "in"
plt.rcParams["ytick.direction"] = "in"


def plotspline(path, label=None, color="red"):
    data = np.loadtxt(path)
    df = pd.DataFrame(data, columns=["idx", "distance", "energy", "force"])
    x = np.array(df["idx"])
    y = np.array(df["energy"])
    plt.plot(x, y, c=color, linewidth=1, label=label)


def plotneb(path, color="blue"):
    data = np.loadtxt(path)
    df = pd.DataFrame(data, columns=["idx", "distance", "energy", "force", "label"])
    x = np.array(df["idx"])
    y = np.array(df["energy"])
    plt.scatter(x, y, c=color)


def main():

    plt.figure(figsize=(8, 6), dpi=300)
    ### ------- 输入文件及标签 -------- ###
    plotspline(path="./spline.dat", label="CrMoB-Mo")
    plotneb(path="./neb.dat")
    ### ------------------------------- ###
    plt.xlabel(r"Reaction Coordinate / $Å$")
    plt.ylabel(r"Energy / $eV$")
    plt.xlim(0, 6)
    # plt.ylim(0,)
    plt.xticks(fontsize=8)
    plt.yticks(fontsize=8)
    plt.legend()
    plt.savefig("neb.png", bbox_inches="tight")


if __name__ == "__main__":
    main()
