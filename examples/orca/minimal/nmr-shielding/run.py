"""用法：python3 run.py；ORCA_EXEC 指向驱动，按 stages.json 顺序运行。"""

import json
import os
import shutil
import subprocess
from pathlib import Path

exe = shutil.which(os.environ.get("ORCA_EXEC", "orca"))
if not exe:
    raise SystemExit("找不到 ORCA")
for stage in json.loads(Path("stages.json").read_text()):
    work = Path(stage)
    if work.exists():
        raise SystemExit(f"{stage} 已存在，请用干净目录")
    work.mkdir()
    shutil.copy("structure.xyz", work / "structure.xyz")
    shutil.copy(stage + ".inp", work / "orca.inp")
    # ORCA 由串行驱动启动，勿再套 mpirun。
    with (work / "orca.out").open("w") as out:
        subprocess.run(
            [exe, "orca.inp"],
            cwd=work,
            stdout=out,
            stderr=subprocess.STDOUT,
            check=True,
        )
