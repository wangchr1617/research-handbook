"""用法：python3 run.py [--ranks 2]；生成整体/片段目录，计算并做差分电荷分析。"""

import argparse
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ranks", type=int, default=1)
    args = parser.parse_args()
    if args.ranks < 1:
        parser.error("MPI 进程数须为正整数")
    root = Path.cwd()
    potential = (root / "POTCAR").read_bytes()
    blocks = re.findall(rb".*?End of Dataset\s*\n", potential, re.DOTALL)
    if len(blocks) != 2 or b"Na_pv" not in blocks[0] or b"PAW_PBE Cl " not in blocks[1]:
        raise SystemExit("请按 Na_pv、Cl 顺序准备本例 POTCAR")
    executable = os.environ.get("VASP_EXEC", "vasp_std")
    command = (
        [executable]
        if args.ranks == 1
        else ["mpirun", "-np", str(args.ranks), executable]
    )
    for name, poscar, pot in [
        ("combined", "POSCAR", potential),
        ("na", "POSCAR.na", blocks[0]),
        ("cl", "POSCAR.cl", blocks[1]),
    ]:
        work = root / name
        work.mkdir(exist_ok=True)
        if (work / "OUTCAR").exists():
            raise SystemExit(f"{name} 已有输出，请使用新目录或只运行后处理")
        shutil.copy2(root / poscar, work / "POSCAR")
        for filename in ["INCAR", "KPOINTS"]:
            shutil.copy2(root / filename, work / filename)
        (work / "POTCAR").write_bytes(pot)
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
