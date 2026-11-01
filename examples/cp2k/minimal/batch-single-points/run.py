"""用法：python3 run.py [--ranks 2]；顺序计算两个水分子结构并汇总能量与力。"""

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path

CASES = (
    "water-reference",
    "water-stretched",
)  # 待标注的独立结构，各目录含 structure.xyz。


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ranks", type=int, default=1)
    args = parser.parse_args()
    if args.ranks < 1:
        parser.error("MPI 进程数须为正整数")
    root = Path.cwd()
    executable = os.environ.get("CP2K_EXEC", "cp2k.psmp")
    command = (
        [executable]
        if args.ranks == 1
        else ["mpirun", "-np", str(args.ranks), executable]
    )
    for name in CASES:
        directory = root / "runs" / name
        directory.mkdir(parents=True, exist_ok=True)
        if (directory / "cp2k.out").exists():
            raise SystemExit(f"{name} 已有输出，请使用新目录或只做后处理")
        shutil.copy2(root / "cp2k.inp", directory / "cp2k.inp")
        shutil.copy2(root / name / "structure.xyz", directory / "structure.xyz")
        with (directory / "launch.log").open("w") as log:
            subprocess.run(
                command + ["-i", "cp2k.inp", "-o", "cp2k.out"],
                cwd=directory,
                stdout=log,
                stderr=subprocess.STDOUT,
                check=True,
            )
    subprocess.run([sys.executable, "postprocess.py"], check=True)


if __name__ == "__main__":
    main()
