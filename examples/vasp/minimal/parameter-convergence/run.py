"""用法：python3 run.py [--ranks 2]；分别扫描截断能与规则 k 网格。"""

import argparse
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

CUTOFFS_EV = (350, 450, 550)  # 固定 7³ k 网格测试截断能。
K_MESHES = (5, 7, 9, 11, 13)  # 固定 ENCUT=450 eV 测试 k 网格。


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
    cases = sorted(
        {(cutoff, 7) for cutoff in CUTOFFS_EV} | {(450, mesh) for mesh in K_MESHES}
    )
    for cutoff, mesh in cases:
        work = root / f"encut-{cutoff}-k-{mesh}"
        if work.exists():
            raise SystemExit(f"{work.name} 已存在，请使用新目录或只做后处理")
        work.mkdir()
        incar = re.sub(
            r"(?m)^ENCUT\s*=.*$", f"ENCUT = {cutoff}", (root / "INCAR").read_text()
        )
        (work / "INCAR").write_text(incar)
        (work / "KPOINTS").write_text(
            f"Gamma-centered convergence grid\n0\nGamma\n{mesh} {mesh} {mesh}\n0 0 0\n"
        )
        for name in ["POSCAR", "POTCAR"]:
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
