"""用法：python3 run.py；小LJ晶体中心差分弹性，LMP_EXEC 可指定程序。"""

import json
import os
import shutil
import subprocess
from pathlib import Path

exe = shutil.which(os.environ.get("LMP_EXEC", "lmp"))
if not exe:
    raise SystemExit("找不到 LAMMPS")
for stage in json.loads(Path("stages.json").read_text()):
    work = Path(stage)
    if work.exists():
        raise SystemExit(f"{stage} 已存在")
    work.mkdir()
    shutil.copy(stage + ".in", work / "in.lammps")
    if stage != "prepare":
        shutil.copy("prepare/equilibrated.data", work / "equilibrated.data")
    with (work / "lammps.out").open("w") as out:
        subprocess.run(
            [exe, "-in", "in.lammps"],
            cwd=work,
            stdout=out,
            stderr=subprocess.STDOUT,
            check=True,
        )
