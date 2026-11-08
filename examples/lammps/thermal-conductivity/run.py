"""用法：python3 run.py；依次执行 EMD 与 NEMD，LMP_EXEC 可指定 LAMMPS 程序。"""

import os
import shutil
import subprocess
from pathlib import Path

here = Path(__file__).resolve().parent
exe = shutil.which(os.environ.get("LMP_EXEC", "lmp"))
if not exe:
    raise SystemExit("找不到 LAMMPS，请设置 LMP_EXEC")
for stage in ("emd", "nemd"):
    log = here / f"log.{stage}"
    if log.exists():
        log.unlink()
    with (here / f"stdout.{stage}").open("w") as out:
        subprocess.run(
            [exe, "-in", f"in.{stage}", "-log", f"log.{stage}"],
            cwd=here,
            stdout=out,
            stderr=subprocess.STDOUT,
            check=True,
        )
    if "Total wall time:" not in (here / f"stdout.{stage}").read_text():
        raise SystemExit(f"{stage} 未正常结束")
print("计算完成：python3 postprocess.py")
