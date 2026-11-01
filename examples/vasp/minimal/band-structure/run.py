"""用法：python3 run.py [--ranks 2]；依次完成 SCF、固定电荷能带与 VASPKIT 导出。"""

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ranks", type=int, default=1)
    args = parser.parse_args()
    root = Path.cwd()
    if not (root / "POTCAR").is_file():
        raise SystemExit("请先按 POTCAR.spec 准备授权 POTCAR")
    executable = os.environ.get("VASP_EXEC", "vasp_std")
    command = (
        [executable]
        if args.ranks == 1
        else ["mpirun", "-np", str(args.ranks), executable]
    )
    for stage in ["scf", "band"]:
        work = root / stage
        work.mkdir(exist_ok=True)
        for name in ["POSCAR", "POTCAR"]:
            shutil.copy2(root / name, work / name)
        for name in ["INCAR", "KPOINTS"]:
            shutil.copy2(root / f"{name}.{stage}", work / name)
        if stage == "band":
            shutil.copy2(root / "scf/CHGCAR", work / "CHGCAR")
        with (work / "vasp.log").open("w") as log:
            subprocess.run(
                command, cwd=work, stdout=log, stderr=subprocess.STDOUT, check=True
            )
        subprocess.run(
            [sys.executable, str(root / "check_vasp.py")], cwd=work, check=True
        )
    shutil.copy2(root / "vaspkit.in", root / "band/vaspkit.in")
    subprocess.run(
        [sys.executable, str(root / "postprocess.py")], cwd=root / "band", check=True
    )


if __name__ == "__main__":
    main()
