"""用法：python3 run.py [--ranks 2]；用 phono3py 生成受力任务并计算晶格热导率。"""

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path

import numpy as np
from phono3py import Phono3py
from phonopy.interface.vasp import read_vasp, write_vasp

SUPERCELL = (2, 2, 2)  # 16 原子硅超胞，用于二阶和三阶力常数。
DISPLACEMENT_A = 0.03  # 位移幅度，Å。
PAIR_CUTOFF_A = 3.0  # 三阶位移对的距离截断，Å；研究计算需检查截断收敛。


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ranks", type=int, default=1)
    args = parser.parse_args()
    if args.ranks < 1:
        parser.error("MPI 进程数须为正整数")
    root = Path.cwd()
    if not (root / "POTCAR").is_file():
        raise SystemExit("请准备授权 Si POTCAR")
    if (root / "phono3py_disp.yaml").exists():
        raise SystemExit("已有位移任务，请使用新目录，或仅运行后处理")
    phonon = Phono3py(
        read_vasp("POSCAR"),
        np.diag(SUPERCELL),
        phonon_supercell_matrix=np.diag(SUPERCELL),
    )
    phonon.generate_displacements(
        distance=DISPLACEMENT_A, is_plusminus="auto", cutoff_pair_distance=PAIR_CUTOFF_A
    )
    phonon.save(filename="phono3py_disp.yaml")
    executable = os.environ.get("VASP_EXEC", "vasp_std")
    command = (
        [executable]
        if args.ranks == 1
        else ["mpirun", "-np", str(args.ranks), executable]
    )
    cells = [
        (index, cell)
        for index, cell in enumerate(phonon.supercells_with_displacements, 1)
        if cell is not None
    ]
    print(f"受力任务数：{len(cells)}", flush=True)
    for done, (index, cell) in enumerate(cells, 1):
        work = root / f"disp-{index:05d}"
        work.mkdir()
        write_vasp(str(work / "POSCAR"), cell)
        for name in ["INCAR", "KPOINTS", "POTCAR"]:
            shutil.copy2(root / name, work / name)
        with (work / "vasp.log").open("w") as log:
            subprocess.run(
                command, cwd=work, stdout=log, stderr=subprocess.STDOUT, check=True
            )
        subprocess.run(
            [sys.executable, str(root / "check_vasp.py")], cwd=work, check=True
        )
        print(f"已完成 {done}/{len(cells)}：{work.name}", flush=True)
    subprocess.run([sys.executable, "postprocess.py"], check=True)


if __name__ == "__main__":
    main()
