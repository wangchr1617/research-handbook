"""用法：python3 run.py [--ranks 2]；计算五个体积下的静态能量及 Phonopy 正负位移受力。"""

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path

import numpy as np
from phonopy import Phonopy
from phonopy.interface.vasp import read_vasp, write_vasp

VOLUME_RATIOS = (0.96, 0.98, 1.0, 1.02, 1.04)  # 相对 POSCAR 的体积比，不是晶格长度比。
DISPLACEMENT_A = 0.01  # 原子位移幅度，单位 Å。
SUPERCELL = (2, 2, 2)  # 两原子原胞扩成 16 原子超胞。


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
    original = read_vasp("POSCAR")
    for ratio in VOLUME_RATIOS:
        work = root / f"volume-{round(ratio * 1000):04d}"
        if work.exists():
            raise SystemExit(f"{work.name} 已存在，请在新目录运行或只做后处理")
        work.mkdir()
        unitcell = original.copy()
        unitcell.cell = original.cell * ratio ** (1 / 3)
        phonon = Phonopy(unitcell, np.diag(SUPERCELL))
        phonon.generate_displacements(distance=DISPLACEMENT_A, is_plusminus=True)
        phonon.save(filename=str(work / "phonopy_disp.yaml"))
        calculations = [("static", phonon.supercell)] + [
            (f"disp-{i:03d}", cell)
            for i, cell in enumerate(phonon.supercells_with_displacements, 1)
        ]
        for name, structure in calculations:
            directory = work / name
            directory.mkdir()
            write_vasp(str(directory / "POSCAR"), structure)
            for filename in ["INCAR", "KPOINTS", "POTCAR"]:
                shutil.copy2(root / filename, directory / filename)
            with (directory / "vasp.log").open("w") as log:
                subprocess.run(
                    command,
                    cwd=directory,
                    stdout=log,
                    stderr=subprocess.STDOUT,
                    check=True,
                )
            subprocess.run(
                [sys.executable, str(root / "check_vasp.py")], cwd=directory, check=True
            )
        print(f"已完成体积比 {ratio:g}", flush=True)
    subprocess.run([sys.executable, "postprocess.py"], check=True)


if __name__ == "__main__":
    main()
