"""用法：python3 run.py [--ranks 2] [--reuse 既有案例目录]；H/Al(111) 参考态与吸附态。"""

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path

CASES = {
    "clean": ("clean", "slab", ["Al"]),
    "half": ("ads", "slab", ["Al", "H"]),
    "full": ("ads", "slab", ["Al", "H"]),
    "h2": ("h2", "h2", ["H"]),
}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--ranks", type=int, default=1)
    p.add_argument("--reuse", type=Path)
    a = p.parse_args()
    if a.ranks < 1:
        p.error("MPI 进程数须为正整数")
    root = Path.cwd()
    if a.reuse:
        subprocess.run(
            [sys.executable, "postprocess.py", "--source", str(a.reuse.resolve())],
            check=True,
        )
        return
    for element in ["Al", "H"]:
        if not (root / "potentials" / element / "POTCAR").is_file():
            raise SystemExit(f"请准备 potentials/{element}/POTCAR 授权数据")
    exe = os.environ.get("VASP_EXEC", "vasp_std")
    cmd = [exe] if a.ranks == 1 else ["mpirun", "-np", str(a.ranks), exe]
    for name, (incar, kmesh, elements) in CASES.items():
        work = root / name
        if work.exists():
            raise SystemExit(f"{name} 已存在，请使用新目录或 --reuse")
        work.mkdir()
        shutil.copy2(root / f"POSCAR.{name}", work / "POSCAR")
        shutil.copy2(root / f"INCAR.{incar}", work / "INCAR")
        shutil.copy2(root / f"KPOINTS.{kmesh}", work / "KPOINTS")
        (work / "POTCAR").write_bytes(
            b"".join(
                (root / "potentials" / e / "POTCAR").read_bytes() for e in elements
            )
        )
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
