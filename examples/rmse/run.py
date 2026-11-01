"""运行：python3 examples/rmse/run.py；仅依赖 Python 3 标准库。"""
import csv
from math import isfinite, sqrt
from pathlib import Path


def main():
    with Path(__file__).with_name("data.csv").open(newline="", encoding="utf-8") as stream:
        pairs = [(float(row["reference"]), float(row["prediction"]))
                 for row in csv.DictReader(stream)]
    if not pairs or not all(isfinite(value) for pair in pairs for value in pair):
        raise ValueError("数据须包含至少一行有限数值")
    rmse = sqrt(sum((pred - ref) ** 2 for ref, pred in pairs) / len(pairs))
    print(f"Samples: {len(pairs)}")
    print(f"RMSE: {rmse:.6f} eV/atom")


if __name__ == "__main__":
    main()
