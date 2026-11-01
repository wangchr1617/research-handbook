"""用法：python3 run.py；CP2K_EXEC 指定程序，CP2K_DATA_DIR 指定安装数据。"""

import json
import os
import shutil
import subprocess
from pathlib import Path

exe = shutil.which(os.environ.get("CP2K_EXEC", "cp2k.psmp"))
if not exe:
    raise SystemExit("找不到 CP2K")
for stage in json.loads(Path("stages.json").read_text()):
    work = Path(stage)
    if work.exists():
        raise SystemExit(f"{stage} 已存在，请使用干净目录")
    work.mkdir()
    shutil.copy("structure.xyz", work / "structure.xyz")
    shutil.copy(stage + ".inp", work / "cp2k.inp")
    with (work / "cp2k.stdout").open("w") as out:
        subprocess.run(
            [exe, "-i", "cp2k.inp", "-o", "cp2k.out"],
            cwd=work,
            stdout=out,
            stderr=subprocess.STDOUT,
            check=True,
        )
