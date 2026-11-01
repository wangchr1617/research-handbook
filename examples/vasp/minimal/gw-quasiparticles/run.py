"""用法：python3 run.py [--ranks 2]；按依赖顺序运行小体系多体计算。"""

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path

STAGES = ["scf", "exact", "gw"]


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--ranks", type=int, default=1)
    a = p.parse_args()
    if a.ranks < 1:
        p.error("MPI 进程数须为正整数")
    root = Path.cwd()
    exe = os.environ.get("VASP_EXEC", "vasp_std")
    cmd = [exe] if a.ranks == 1 else ["mpirun", "-np", str(a.ranks), exe]
    for stage in STAGES:
        work = root / stage
        if work.exists():
            raise SystemExit(f"{stage} 已存在，请使用新目录或只做后处理")
        work.mkdir()
        for f in ["POSCAR", "KPOINTS", "POTCAR"]:
            shutil.copy2(root / f, work / f)
        shutil.copy2(root / f"INCAR.{stage}", work / "INCAR")
        if stage == "exact":
            for f in ["WAVECAR", "CHGCAR"]:
                shutil.copy2(root / "scf" / f, work / f)
        elif stage != "scf":
            source = root / ("gw" if stage == "bse" else "exact")
            for f in ["WAVECAR", "WAVEDER"]:
                shutil.copy2(source / f, work / f)
            if stage == "bse":
                kernels = list(source.glob("WFULL*.tmp"))
                if not kernels:
                    raise SystemExit("缺少完整 GW 筛选核")
                for f in source.glob("W*.tmp"):
                    shutil.copy2(f, work / f.name)
        with (work / "vasp.log").open("w") as log:
            subprocess.run(
                cmd, cwd=work, stdout=log, stderr=subprocess.STDOUT, check=True
            )
        if "General timing and accounting" not in (work / "OUTCAR").read_text(
            errors="replace"
        ):
            raise SystemExit(f"{stage} 未正常结束")
        if stage == "scf":
            subprocess.run(
                [sys.executable, str(root / "check_vasp.py")], cwd=work, check=True
            )
    subprocess.run([sys.executable, "postprocess.py"], check=True)


if __name__ == "__main__":
    main()
