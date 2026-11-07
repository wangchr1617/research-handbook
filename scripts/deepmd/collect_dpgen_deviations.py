"""收集 DP-GEN 的最大原子力偏差。用法：python collect_dpgen_deviations.py ROOT -o deviations.csv。

读取 model_devi.out 的 max_devi_f 列；--column 可指定零起始列号。
不再把同一批数据重复写成多个温度文件，来源路径保留在 CSV 中。
"""

import argparse
import csv
import math
from pathlib import Path


def collect(root, column=None):
    if column is not None and column < 0:
        raise ValueError("列号不能为负")
    if not root.is_dir():
        raise ValueError("输入目录不存在")
    rows = []
    for path in sorted(root.rglob("model_devi.out")):
        selected = column
        for number, line in enumerate(path.read_text().splitlines(), 1):
            if not line.strip():
                continue
            if line.lstrip().startswith("#"):
                header = line.lstrip().lstrip("#").split()
                if column is None and "max_devi_f" in header:
                    selected = header.index("max_devi_f")
                continue
            if selected is None:
                raise ValueError(f"{path} 无 max_devi_f 表头，请使用 --column 指定列号")
            values = line.split()
            try:
                raw_step, deviation = float(values[0]), float(values[selected])
                if (
                    not math.isfinite(raw_step)
                    or not raw_step.is_integer()
                    or raw_step < 0
                ):
                    raise ValueError("步号必须为非负整数")
                if not math.isfinite(deviation) or deviation < 0:
                    raise ValueError("偏差必须为有限非负数")
                step = int(raw_step)
            except (IndexError, ValueError) as error:
                raise ValueError(f"{path}:{number} 数据格式错误") from error
            rows.append({"source": str(path), "step": step, "max_devi_f": deviation})
    if not rows:
        raise ValueError("没有找到可读取的 model_devi.out 数据")
    return rows


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", type=Path, nargs="?", default=Path("."))
    parser.add_argument("-o", "--output", type=Path, default=Path("deviations.csv"))
    parser.add_argument("--column", type=int, help="零起始列号；通常为 4")
    args = parser.parse_args()
    if args.column is not None and args.column < 0:
        parser.error("列号不能为负")
    if args.output.exists() or args.output.is_symlink():
        parser.error("输出文件已存在")
    try:
        rows = collect(args.root, args.column)
        with args.output.open("x", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=["source", "step", "max_devi_f"])
            writer.writeheader()
            writer.writerows(rows)
    except (ValueError, OSError) as error:
        parser.exit(1, f"错误：{error}\n")


if __name__ == "__main__":
    main()
