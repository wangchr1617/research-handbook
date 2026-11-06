"""从实际数值表重绘：python plot_results.py CASE DATA_DIR --output /tmp/figure.png。"""

import argparse
import os
from pathlib import Path
import tempfile

from run_case import CASES, plot_case


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("case", choices=CASES)
    parser.add_argument("data", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        parser.error("输出图片已存在，请选择新文件名")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="materials-plot-") as cache:
        os.environ["MPLCONFIGDIR"] = cache
        os.environ["XDG_CACHE_HOME"] = cache
        plot_case(args.case, args.data, args.output)


if __name__ == "__main__":
    main()
