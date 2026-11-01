"""检查 GPUMD 子任务输出。用法：python check_gpumd.py ROOT -o status.csv。

检查 output 中的结束标记，统计 dump.xyz 的完整帧数；不改写或删除任务文件。
"""

import argparse
import csv
from pathlib import Path


def frame_count(path):
    count = 0
    with path.open() as stream:
        while line := stream.readline():
            if not line.strip():
                continue
            natoms = int(line)
            if natoms <= 0 or not stream.readline():
                raise ValueError(f"{path} 帧头无效")
            for _ in range(natoms):
                if not stream.readline():
                    raise ValueError(f"{path} 最后一帧不完整")
            count += 1
    return count


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", type=Path, nargs="?", default=Path("."))
    parser.add_argument("-o", "--output", type=Path, default=Path("gpumd-status.csv"))
    args = parser.parse_args()
    if args.output.exists():
        parser.error("输出文件已存在")
    rows = []
    for directory in sorted(p for p in args.root.iterdir() if p.is_dir()):
        output, dump = directory / "output", directory / "dump.xyz"
        text = output.read_text(errors="replace") if output.exists() else ""
        times = [line.strip() for line in text.splitlines() if "Time used =" in line]
        try:
            frames, error = frame_count(dump) if dump.exists() else 0, ""
        except ValueError as exception:
            frames, error = "", str(exception)
        rows.append(
            {
                "directory": directory.name,
                "output_exists": output.exists(),
                "finished": "Finished running" in text,
                "time": times[-1] if times else "",
                "frames": frames,
                "error": error,
            }
        )
    with args.output.open("w", newline="") as stream:
        writer = csv.DictWriter(
            stream,
            fieldnames=[
                "directory",
                "output_exists",
                "finished",
                "time",
                "frames",
                "error",
            ],
        )
        writer.writeheader()
        writer.writerows(rows)


if __name__ == "__main__":
    main()
