"""用法：python3 run.py [--ranks 2]；需读取三整数 OPTCELL 的专用 VASP。"""

import argparse
import os
import subprocess
import sys
from pathlib import Path


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--ranks", type=int, default=1)
    a = p.parse_args()
    if a.ranks < 1:
        p.error("MPI 进程数须为正整数")
    if Path("OUTCAR").exists():
        raise SystemExit("OUTCAR 已存在，请使用新目录或只做后处理")
    exe = os.environ.get("VASP_EXEC", "vasp_optcell")
    command = [exe] if a.ranks == 1 else ["mpirun", "-np", str(a.ranks), exe]
    with Path("vasp.log").open("w") as log:
        subprocess.run(command, stdout=log, stderr=subprocess.STDOUT, check=True)
    subprocess.run([sys.executable, "postprocess.py"], check=True)


if __name__ == "__main__":
    main()
