"""用法：python3 run.py [--ranks 2]；Dimer 搜索后以有限差分确认鞍点。"""

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path

p = argparse.ArgumentParser(description=__doc__)
p.add_argument("--ranks", type=int, default=1)
a = p.parse_args()
if a.ranks < 1:
    p.error("MPI 进程数须为正整数")
exe = os.environ.get("VASP_EXEC", "vasp_std")
cmd = [exe] if a.ranks == 1 else ["mpirun", "-np", str(a.ranks), exe]
if Path("OUTCAR").exists() or Path("frequency").exists():
    raise SystemExit("请在干净目录运行，避免覆盖已有结果")
with open("vasp.log", "w") as log:
    subprocess.run(cmd, stdout=log, stderr=subprocess.STDOUT, check=True)
subprocess.run([sys.executable, "check_vasp.py"], check=True)
work = Path("frequency")
work.mkdir()
for source, target in [
    ("CONTCAR", "POSCAR"),
    ("INCAR.frequency", "INCAR"),
    ("POTCAR", "POTCAR"),
    ("KPOINTS", "KPOINTS"),
]:
    shutil.copy2(source, work / target)
with (work / "vasp.log").open("w") as log:
    subprocess.run(cmd, cwd=work, stdout=log, stderr=subprocess.STDOUT, check=True)
subprocess.run([sys.executable, "postprocess.py"], check=True)
