"""用法：python3 run.py [--ranks 2]；非周期水二聚体的 PBE/D3(BJ) 对照。"""

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--ranks", type=int, default=1)
    a = p.parse_args()
    if a.ranks < 1:
        p.error("MPI 进程数须为正整数")
    root = Path.cwd()
    exe = os.environ.get("CP2K_EXEC", "cp2k.psmp")
    cmd = [exe] if a.ranks == 1 else ["mpirun", "-np", str(a.ranks), exe]
    for name in ["pbe", "d3"]:
        work = root / name
        if work.exists():
            raise SystemExit(f"{name} 已存在，请使用新目录或只做后处理")
        work.mkdir()
        shutil.copy2(root / "structure.xyz", work / "structure.xyz")
        shutil.copy2(root / f"cp2k.{name}.inp", work / "cp2k.inp")
        with (work / "launch.log").open("w") as log:
            subprocess.run(
                cmd + ["-i", "cp2k.inp", "-o", "cp2k.out"],
                cwd=work,
                stdout=log,
                stderr=subprocess.STDOUT,
                check=True,
            )
        subprocess.run(
            [sys.executable, str(root / "check_cp2k.py")], cwd=work, check=True
        )
    subprocess.run([sys.executable, "postprocess.py"], check=True)


if __name__ == "__main__":
    main()
