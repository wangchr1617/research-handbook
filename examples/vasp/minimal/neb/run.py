"""用法：python3 run.py --ranks 3 [--stage endpoints|neb|all]；用 VTST 准备并运行 CI-NEB。"""

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ranks", type=int, default=3)
    parser.add_argument("--stage", choices=["endpoints", "neb", "all"], default="all")
    args = parser.parse_args()
    if args.ranks <= 0 or args.ranks % 3:
        raise SystemExit("本例 IMAGES=3，总 MPI 进程数须为 3 的倍数")
    root = Path.cwd()
    if not (root / "POTCAR").is_file():
        raise SystemExit("请先按 POTCAR.spec 准备授权势")
    executable = os.environ.get("VASP_EXEC", "vasp_vtst")  # 需支持 VTST 的 VASP。
    if args.stage in ["endpoints", "all"]:
        for name in ["initial", "final"]:
            work = root / name
            work.mkdir(exist_ok=True)
            if (work / "OUTCAR").exists():
                raise SystemExit(f"{work} 已有计算输出，请使用新的工作目录")
            for source, target in [
                (f"POSCAR.{name}", "POSCAR"),
                ("INCAR.endpoint", "INCAR"),
                ("KPOINTS", "KPOINTS"),
                ("POTCAR", "POTCAR"),
            ]:
                shutil.copy2(root / source, work / target)
            # 端点任务很小，单进程即可；NEB 阶段再按插点分配 MPI 进程。
            with (work / "vasp.log").open("w") as log:
                subprocess.run(
                    [executable],
                    cwd=work,
                    stdout=log,
                    stderr=subprocess.STDOUT,
                    check=True,
                )
            subprocess.run(
                [sys.executable, str(root / "check_vasp.py")], cwd=work, check=True
            )
            if "reached required accuracy" not in (work / "OUTCAR").read_text():
                raise SystemExit(f"{name} 端点未收敛")
    if args.stage == "endpoints":
        return
    for name in ["initial", "final"]:
        if "reached required accuracy" not in (root / name / "OUTCAR").read_text():
            raise SystemExit(f"{name} 端点未收敛，不能开始 NEB")
    if Path("neb.log").exists():
        raise SystemExit("neb.log 已存在，请使用新的工作目录或仅重跑后处理")
    nebmake = os.environ.get("NEBMAKE_EXEC", "nebmake.pl")
    subprocess.run([nebmake, "initial/CONTCAR", "final/CONTCAR", "3"], check=True)
    for stage, image in [("initial", "00"), ("final", "04")]:
        for name in ["OUTCAR", "CONTCAR"]:
            shutil.copy2(root / stage / name, root / image / name)
    shutil.copy2(root / "INCAR.neb", root / "INCAR")
    with Path("neb.log").open("w") as log:
        subprocess.run(
            ["mpirun", "-np", str(args.ranks), executable],
            stdout=log,
            stderr=subprocess.STDOUT,
            check=True,
        )
    subprocess.run([sys.executable, "postprocess.py"], check=True)


if __name__ == "__main__":
    main()
