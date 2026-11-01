"""用法：python3 prepare.py；生成完整等间隔费米面网格，分数倒易坐标。"""

import json
from pathlib import Path

import numpy as np

GRID = 9  # 每个方向的独立采样点数；总数 GRID³，不含周期重复端点。


def main():
    points = (
        np.array(np.meshgrid(*([np.arange(GRID) / GRID - 0.5] * 3), indexing="ij"))
        .reshape(3, -1)
        .T
    )
    Path("KPOINTS.grid").write_text(
        "Full reciprocal grid\n"
        + str(len(points))
        + "\nReciprocal\n"
        + "".join(" ".join(f"{v:.12f}" for v in k) + " 1\n" for k in points)
    )
    Path("grid.json").write_text(json.dumps({"grid": GRID}) + "\n")


if __name__ == "__main__":
    main()
