"""用法：python3 run.py [--ranks 2]；NaCl 的两组 FFT 网格计算及 Bader 分析。"""

import argparse
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

GRIDS = (96, 144)  # 细 FFT 网格每个方向的点数，用于比较原子电荷变化。


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ranks", type=int, default=1)
    args = parser.parse_args()
    if args.ranks <= 0:
        raise SystemExit("MPI 进程数须为正整数")
    root = Path.cwd()
    executable = os.environ.get("VASP_EXEC", "vasp_std")
    command = (
        [executable]
        if args.ranks == 1
        else ["mpirun", "-np", str(args.ranks), executable]
    )
    for grid in GRIDS:
        work = root / f"grid-{grid}"
        work.mkdir(exist_ok=True)
        if (work / "OUTCAR").exists():
            raise SystemExit(f"{work} 已有输出，请使用新目录或只运行后处理")
        text = (root / "INCAR").read_text()
        for name in ["NGXF", "NGYF", "NGZF"]:
            text = re.sub(r"(?im)^\s*" + name + r"\s*=.*$", f"{name} = {grid}", text)
        (work / "INCAR").write_text(text)
        for name in ["POSCAR", "KPOINTS", "POTCAR"]:
            shutil.copy2(root / name, work / name)
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
