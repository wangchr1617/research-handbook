"""用法：python3 run.py；LMP_EXEC 可指定程序，输出原生压力自相关。"""

import os
import shutil
import subprocess
from pathlib import Path

if Path("lammps.out").exists():
    raise SystemExit("请使用干净目录")
exe = shutil.which(os.environ.get("LMP_EXEC", "lmp"))
if not exe:
    raise SystemExit("找不到 LAMMPS")
with Path("lammps.out").open("w") as out:
    subprocess.run(
        [exe, "-in", "in.lammps"], stdout=out, stderr=subprocess.STDOUT, check=True
    )
