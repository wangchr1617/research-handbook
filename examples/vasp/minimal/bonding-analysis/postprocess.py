"""用法：python3 postprocess.py；检查非自旋 COHP/COOP 数据并绘制平均 −COHP。"""

import json
import re
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

SPILLING_LIMIT_PERCENT = 5.0  # 小案例投影检查门槛，正式分析还须测试局域基组。


def read_curve(filename):
    lines = Path(filename).read_text().splitlines()
    header = lines[1].split()
    pairs, spins, points = map(int, header[:3])
    if spins != 1:
        raise SystemExit("本绘图入口仅适用于非自旋案例")
    data = np.loadtxt(lines[-points:], ndmin=2)
    if (
        data.shape != (points, 1 + 2 * pairs)
        or not np.isfinite(data).all()
        or not np.all(np.diff(data[:, 0]) > 0)
    ):
        raise SystemExit(f"{filename} 数据布局或能量轴异常")
    return data


def main():
    text = Path("lobsterout").read_text(errors="replace")
    spill = [
        float(v)
        for v in re.findall(r"(?i)charge spilling\s*[:=]\s*([0-9.]+)\s*%", text)
    ]
    if not spill or max(spill) > SPILLING_LIMIT_PERCENT:
        raise SystemExit("电荷泄漏缺失或偏大，请检查投影和基组")
    cohp = read_curve("COHPCAR.lobster")
    coop = read_curve("COOPCAR.lobster")
    if not np.allclose(cohp[:, 0], coop[:, 0]):
        raise SystemExit("COHP/COOP 能量轴不一致")
    if not Path("ICOHPLIST.lobster").is_file():
        raise SystemExit("缺少键积分列表")
    Path("bonding-results.json").write_text(
        json.dumps(
            {"charge_spilling_percent": spill, "energy_points": len(cohp)}, indent=2
        )
        + "\n"
    )
    fig, ax = plt.subplots(figsize=(5, 4), layout="constrained")
    ax.plot(-cohp[:, 1], cohp[:, 0])
    ax.axhline(0, color=".5", linestyle="--")
    ax.axvline(0, color=".5", linewidth=0.7)
    ax.set(
        xlabel="Average −COHP (eV per bond)",
        ylabel="E − E(F) (eV)",
        title="Si | nearest-neighbour bonding",
    )
    fig.savefig("si-cohp.png", dpi=220)


if __name__ == "__main__":
    main()
