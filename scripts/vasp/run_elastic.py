"""批量运行各 cij/strain_* 的优化脚本，不提交集群任务。

用法：python run_elastic.py ROOT --script opt_ion.py --model nep.txt
依赖由 --script 指定的优化程序；其标准输出写到各任务的 OUTCAR。
"""

import argparse
import shutil
import subprocess
import sys
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", type=Path)
    parser.add_argument("--script", type=Path, required=True, help="优化程序路径")
    parser.add_argument("--model", type=Path, required=True, help="NEP 模型路径")
    args = parser.parse_args()
    script, model = args.script.resolve(), args.model.resolve()
    if not script.is_file() or not model.is_file():
        parser.error("脚本或模型不存在")
    jobs = sorted(p for p in args.root.glob("*/strain_*") if p.is_dir())
    if not jobs:
        parser.error("未找到 cij/strain_* 目录")
    if any(
        (job / name).exists()
        for job in jobs
        for name in (script.name, "nep.txt", "OUTCAR")
    ):
        parser.error("任务目录中已有脚本、模型或 OUTCAR，请先检查")
    for job in jobs:
        shutil.copy2(script, job / script.name)
        shutil.copy2(model, job / "nep.txt")
        with (job / "OUTCAR").open("w") as stream:
            subprocess.run(
                [sys.executable, script.name], cwd=job, stdout=stream, check=True
            )


if __name__ == "__main__":
    main()
