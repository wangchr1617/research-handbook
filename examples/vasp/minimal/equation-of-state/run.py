"""用法：python3 run.py [--ranks 2]；扫描硅原胞体积，调用 VASPKIT 拟合状态方程。"""

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path

from ase.io import read, write

VOLUME_RATIOS = (0.94, 0.97, 1.00, 1.03, 1.06)  # 体积比例，不是晶格边长比例。


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ranks", type=int, default=1)
    args = parser.parse_args()
    root = Path.cwd()
    if not (root / "POTCAR").is_file():
        raise SystemExit("请先按 POTCAR.spec 准备授权 Si POTCAR")
    original = read("POSCAR", format="vasp")
    executable = os.environ.get("VASP_EXEC", "vasp_std")
    command = (
        [executable]
        if args.ranks == 1
        else ["mpirun", "-np", str(args.ranks), executable]
    )
    for ratio in VOLUME_RATIOS:
        work = root / f"volume-{ratio:.2f}"
        work.mkdir(exist_ok=True)
        atoms = original.copy()
        atoms.set_cell(original.cell * ratio ** (1 / 3), scale_atoms=True)
        write(work / "POSCAR", atoms, format="vasp", direct=True)
        for name in ["INCAR", "KPOINTS", "POTCAR"]:
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
