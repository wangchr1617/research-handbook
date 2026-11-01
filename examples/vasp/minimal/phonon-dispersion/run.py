"""用法：python3 run.py [--ranks 2]；由 Phonopy 建立正负位移、计算受力并后处理。"""

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
    if not Path("POTCAR").is_file():
        raise SystemExit("请先准备授权 Si POTCAR，并安装 Phonopy")
    subprocess.run(
        ["phonopy-init", "-d", "--dim", "2", "2", "2", "--amplitude", "0.01", "--pm"],
        check=True,
    )
    executable = os.environ.get("VASP_EXEC", "vasp_std")
    command = (
        [executable]
        if args.ranks == 1
        else ["mpirun", "-np", str(args.ranks), executable]
    )
    root = Path.cwd()
    for structure in sorted(Path(".").glob("POSCAR-*[0-9]")):
        work = Path("disp-" + structure.name.split("-")[-1])
        work.mkdir(exist_ok=True)
        shutil.copy2(structure, work / "POSCAR")
        for name in ["INCAR", "KPOINTS", "POTCAR"]:
            shutil.copy2(name, work / name)
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
