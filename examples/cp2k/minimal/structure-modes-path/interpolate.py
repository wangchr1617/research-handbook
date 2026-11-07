"""从已对应的固定晶胞锚点生成分段线性 NEB 初始副本与 BAND 片段。

用法：python interpolate.py --anchors anchors.json --output-dir NEW
锚点编号从1开始；不自动换原子顺序、平移旋转或选周期映像，不计算 NEB 能垒。
"""

import argparse
import json
from pathlib import Path

import numpy as np


def read_xyz(path):
    lines = Path(path).read_text().splitlines()
    count = int(lines[0])
    rows = [line.split() for line in lines[2:] if line.strip()]
    if len(rows) != count:
        raise ValueError("XYZ 原子数不符")
    elements = [row[0] for row in rows]
    xyz = np.array([[float(v) for v in row[1:]] for row in rows])
    if xyz.shape != (count, 3) or not np.isfinite(xyz).all():
        raise ValueError("坐标列数或数值异常")
    return elements, xyz


def piecewise(anchors):
    indices = [i for i, xyz in anchors]
    if len(indices) < 2 or indices[0] != 1 or indices != sorted(set(indices)):
        raise ValueError("至少两个锚点，序号严格递增且从1开始")
    frames = []
    for (left, x0), (right, x1) in zip(anchors, anchors[1:]):
        if x0.shape != x1.shape:
            raise ValueError("锚点原子数不同")
        for index in range(left, right):
            fraction = (index - left) / (right - left)
            frames.append((1 - fraction) * x0 + fraction * x1)
    frames.append(anchors[-1][1].copy())
    return np.array(frames)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--anchors", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    settings = json.loads(args.anchors.read_text())
    elements, anchors = None, []
    for item in settings["anchors"]:
        names, xyz = read_xyz(args.anchors.parent / item["file"])
        if elements is not None and names != elements:
            raise ValueError("所有锚点的元素与原子顺序必须一致")
        elements = names
        anchors.append((item["index"], xyz))
    frames = piecewise(anchors)
    args.output_dir.mkdir(parents=True, exist_ok=False)
    texts, replica = [], []
    for index, xyz in enumerate(frames, 1):
        name = f"replica-{index:03d}.xyz"
        text = f"{len(elements)}\nPiecewise linear initial NEB image {index}; Angstrom; no energy evaluated\n"
        text += "".join(f"{element} {row[0]:.10f} {row[1]:.10f} {row[2]:.10f}\n" for element, row in zip(elements, xyz))
        (args.output_dir / name).write_text(text)
        texts.append(text)
        replica.append(f"  &REPLICA\n    COORD_FILE_NAME {name}\n  &END REPLICA\n")
    (args.output_dir / "traj.xyz").write_text("".join(texts))
    (args.output_dir / "BAND.inc").write_text(f"NUMBER_OF_REPLICA {len(frames)}\n" + "".join(replica))
    steps = np.linalg.norm(np.diff(frames, axis=0).reshape(len(frames) - 1, -1), axis=1)
    report = dict(images=len(frames), anchor_indices=[i for i, _ in anchors], elements=elements,
                  adjacent_cartesian_norm_angstrom=steps.tolist(),
                  meaning="Initial fixed-cell geometry only; atom mapping, image choice and physical path require review")
    (args.output_dir / "path.json").write_text(json.dumps(report, indent=2) + "\n")
    print(f"产生 {len(frames)} 个副本（含端点）")


if __name__ == "__main__":
    main()
