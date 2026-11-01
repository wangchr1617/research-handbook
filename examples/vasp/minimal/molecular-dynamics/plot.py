"""用法：python3 plot.py；从 OSZICAR 绘制短程 NVT 温度与扩展体系能量。"""

import re
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


def main():
    number = r"([-+0-9.Ee]+)"
    pattern = re.compile(
        r"^\s*(\d+)\s+T=\s*" + number + r"\s+E=\s*" + number, re.MULTILINE
    )
    rows = np.array(
        [
            [float(value) for value in match]
            for match in pattern.findall(Path("OSZICAR").read_text())
        ]
    )
    if rows.ndim != 2 or len(rows) < 2 or not np.isfinite(rows).all():
        raise SystemExit("未找到完整的 MD 温度与能量记录")
    incar = Path("INCAR").read_text()
    timestep = float(re.search(r"(?im)^\s*POTIM\s*=\s*" + number, incar).group(1))
    temperature = float(re.search(r"(?im)^\s*TEBEG\s*=\s*" + number, incar).group(1))
    time = (rows[:, 0] - rows[0, 0]) * timestep  # 以第一帧为时间原点，单位 fs。
    fig, axes = plt.subplots(
        2, 1, figsize=(5.8, 5.8), sharex=True, constrained_layout=True
    )
    axes[0].plot(time, rows[:, 1], "o-", color="#24618c", markersize=4)
    axes[0].axhline(temperature, color="0.4", linestyle="--", label="Thermostat target")
    axes[0].set(ylabel="Temperature (K)", title="Si | short NVT trajectory")
    axes[0].legend(frameon=False)
    axes[1].plot(
        time, (rows[:, 2] - rows[0, 2]) * 1000, "o-", color="#a54828", markersize=4
    )
    axes[1].set(
        xlabel="Time from first frame (fs)", ylabel="Extended-energy change (meV)"
    )
    fig.savefig("si-aimd.png", dpi=240, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print("已生成 si-aimd.png")


if __name__ == "__main__":
    main()
