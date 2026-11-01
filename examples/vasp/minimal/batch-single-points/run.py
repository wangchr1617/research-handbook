"""用法：python3 run.py [--ranks 2]；顺序标注两个硅构型并导出训练数据。"""

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path

CASES = {"reference": "POSCAR", "distorted": "POSCAR.distorted"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ranks", type=int, default=1)
    args = parser.parse_args()
    if args.ranks < 1:
        parser.error("MPI 进程数须为正整数")
    root = Path.cwd()
    if not (root / "POTCAR").is_file():
        raise SystemExit("请先准备授权 Si POTCAR")
    executable = os.environ.get("VASP_EXEC", "vasp_std")
    command = (
        [executable]
        if args.ranks == 1
        else ["mpirun", "-np", str(args.ranks), executable]
    )
    for name, structure in CASES.items():
        work = root / "runs" / name
        if work.exists():
            raise SystemExit(f"{work} 已存在，请使用新目录或只做后处理")
        work.mkdir(parents=True)
        shutil.copy2(root / structure, work / "POSCAR")
        for filename in ["INCAR", "KPOINTS", "POTCAR"]:
            shutil.copy2(root / filename, work / filename)
        with (work / "vasp.log").open("w") as log:
            subprocess.run(
                command, cwd=work, stdout=log, stderr=subprocess.STDOUT, check=True
            )
    subprocess.run([sys.executable, "postprocess.py"], check=True)


if __name__ == "__main__":
    main()
