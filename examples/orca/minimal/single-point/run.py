"""用法：python3 run.py；ORCA_EXEC 可指定 ORCA 驱动，单进程轻量计算。"""

import os
import shutil
import subprocess
from pathlib import Path

if Path("orca.out").exists():
    raise SystemExit("已有计算输出，请使用干净的案例目录")

exe = shutil.which(os.environ.get("ORCA_EXEC", "orca"))
if exe is None:
    raise SystemExit("找不到 ORCA，请设置 ORCA_EXEC")
# ORCA 驱动自行管理并行，不套 mpirun。
with Path("orca.out").open("w") as out:
    subprocess.run([exe, "orca.inp"], stdout=out, stderr=subprocess.STDOUT, check=True)
