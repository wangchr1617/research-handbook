"""用法：python3 run.py [--ranks 2]；顺序计算体相与三种厚度的Al薄膜。"""

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path

STAGES = ["bulk", "slab4", "slab6", "slab8"]
DEFAULT_EXECUTABLE = "vasp_std"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ranks", type=int, default=1)
    args = parser.parse_args()
    if args.ranks < 1:
        parser.error("MPI 进程数须为正整数")
    root = Path.cwd()
    if not (root / "POTCAR").is_file():
        raise SystemExit("请先按 POTCAR.spec 准备授权赝势")
    executable = os.environ.get("VASP_EXEC", DEFAULT_EXECUTABLE)
    command = (
        [executable]
        if args.ranks == 1
        else ["mpirun", "-np", str(args.ranks), executable]
    )
    for stage in STAGES:
        work = root / stage
        if work.exists():
            raise SystemExit(f"{stage} 已存在，请使用新目录或只做后处理")
        work.mkdir()
        kind = "bulk" if stage == "bulk" else "slab"
        for source, target in [
            (f"POSCAR.{stage}", "POSCAR"),
            (f"INCAR.{kind}", "INCAR"),
            (f"KPOINTS.{kind}", "KPOINTS"),
            ("POTCAR", "POTCAR"),
        ]:
            shutil.copy2(root / source, work / target)
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
