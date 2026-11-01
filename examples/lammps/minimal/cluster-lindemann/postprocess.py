"""用法：python3 postprocess.py；流式累计成对距离涨落，计算自由团簇 Lindemann 指标。"""

import json
import subprocess
import sys
from pathlib import Path

import numpy as np
from ase.io import iread

if "Total wall time:" not in Path("lammps.log").read_text():
    raise SystemExit("LAMMPS 未正常结束")
metrics = {}
for state in ["cold", "warm"]:
    count = 0
    mean = np.zeros(1485)
    m2 = np.zeros(1485)
    history = []
    for a in iread(f"cluster.{state}.dump", format="lammps-dump-text"):
        if len(a) != 55 or not np.isfinite(a.positions).all():
            raise SystemExit("粒子数改变或轨迹坐标异常")
        # 自由团簇用普通距离，无最小镜像；dump 已按固定 id 排序。
        displacement = a.positions[:, None] - a.positions[None, :]
        distance = np.linalg.norm(displacement, axis=2)[np.triu_indices(55, 1)]
        if (
            np.min(distance) <= 0
            or np.max(np.linalg.norm(a.positions - a.positions.mean(axis=0), axis=1))
            > 8
        ):
            raise SystemExit("出现重叠或团簇接近模拟盒边界")
        count += 1
        delta = distance - mean
        mean += delta / count
        m2 += delta * (distance - mean)
        if count > 1:
            history.append(
                [
                    (count - 1) * 20 * 0.002,
                    np.mean(np.sqrt(np.maximum(m2 / count, 0)) / mean),
                ]
            )
    if count != 251:
        raise SystemExit("预期初始及250个采样帧")
    index = float(np.mean(np.sqrt(np.maximum(m2 / count, 0)) / mean))
    metrics[state] = {
        "atoms": 55,
        "frames": count,
        "pairs": len(mean),
        "lindemann_index": index,
    }
    np.savetxt(
        f"lindemann.{state}.dat", history, header="time_tau running_all_pair_Lindemann"
    )
if metrics["warm"]["lindemann_index"] <= metrics["cold"]["lindemann_index"]:
    raise SystemExit("升温后距离涨落未增加，请检查采样")
Path("lindemann-results.json").write_text(json.dumps(metrics, indent=2) + "\n")
print(json.dumps(metrics, indent=2))
subprocess.run([sys.executable, "plot.py"], check=True)
