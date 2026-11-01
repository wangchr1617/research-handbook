"""用法：python3 run.py [--ranks 2]；用同一 VASPsol 程序比较真空与连续介质单点。"""

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
    exe = os.environ.get("VASP_EXEC", "vasp_vaspsol")
    command = [exe] if a.ranks == 1 else ["mpirun", "-np", str(a.ranks), exe]
    for name in ["vacuum", "solvent"]:
        work = root / name
        if work.exists():
            raise SystemExit(f"{name} 已存在，请使用新目录或只做后处理")
        work.mkdir()
        for f in ["POSCAR", "POTCAR", "KPOINTS"]:
            shutil.copy2(root / f, work / f)
        shutil.copy2(root / f"INCAR.{name}", work / "INCAR")
        with (work / "vasp.log").open("w") as log:
            subprocess.run(
                command, cwd=work, stdout=log, stderr=subprocess.STDOUT, check=True
            )
        subprocess.run(
            [sys.executable, str(root / "check_vasp.py")], cwd=work, check=True
        )
    subprocess.run([sys.executable, "postprocess.py"], check=True)


if __name__ == "__main__":
    main()
