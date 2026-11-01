"""用法：python3 run.py [--ranks 2] [--vasp-only]；生成波函数后运行授权 LOBSTER。"""

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--ranks", type=int, default=1)
    p.add_argument("--vasp-only", action="store_true")
    a = p.parse_args()
    if a.ranks < 1:
        p.error("MPI 进程数须为正整数")
    lobster = os.environ.get("LOBSTER_EXEC", "lobster")
    if not a.vasp_only and not shutil.which(lobster):
        raise SystemExit("未找到 LOBSTER_EXEC 指定的授权程序")
    if Path("OUTCAR").exists():
        raise SystemExit("OUTCAR 已存在；已有波函数可直接运行 LOBSTER 和后处理")
    exe = os.environ.get("VASP_EXEC", "vasp_std")
    command = [exe] if a.ranks == 1 else ["mpirun", "-np", str(a.ranks), exe]
    with Path("vasp.log").open("w") as log:
        subprocess.run(command, stdout=log, stderr=subprocess.STDOUT, check=True)
    subprocess.run([sys.executable, "check_vasp.py"], check=True)
    if not Path("WAVECAR").is_file() or Path("WAVECAR").stat().st_size < 1000:
        raise SystemExit("缺少有效 WAVECAR")
    if a.vasp_only:
        return
    env = dict(os.environ, OMP_NUM_THREADS=str(a.ranks))
    with Path("lobster.log").open("w") as log:
        subprocess.run(
            [lobster], env=env, stdout=log, stderr=subprocess.STDOUT, check=True
        )
    subprocess.run([sys.executable, "postprocess.py"], check=True)


if __name__ == "__main__":
    main()
