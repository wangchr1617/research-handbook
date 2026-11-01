"""用法：python3 run.py [--ranks 2]；Al 自洽后在完整网格上读取费米面。"""

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
    subprocess.run([sys.executable, "prepare.py"], check=True)
    exe = os.environ.get("VASP_EXEC", "vasp_std")
    cmd = [exe] if a.ranks == 1 else ["mpirun", "-np", str(a.ranks), exe]
    for stage in ["scf", "grid"]:
        work = root / stage
        if work.exists():
            raise SystemExit(f"{stage} 已存在，请使用新目录或只做后处理")
        work.mkdir()
        for f in ["POSCAR", "POTCAR"]:
            shutil.copy2(root / f, work / f)
        for f in ["INCAR", "KPOINTS"]:
            shutil.copy2(root / f"{f}.{stage}", work / f)
        if stage == "grid":
            shutil.copy2(root / "scf/CHGCAR", work / "CHGCAR")
        with (work / "vasp.log").open("w") as log:
            subprocess.run(
                cmd, cwd=work, stdout=log, stderr=subprocess.STDOUT, check=True
            )
        subprocess.run(
            [sys.executable, str(root / "check_vasp.py")], cwd=work, check=True
        )
    subprocess.run([sys.executable, "postprocess.py"], check=True)


if __name__ == "__main__":
    main()
