"""用法：OPENMX_DATA=/path/to/DFT_DATA19 python3 run.py；数据库不复制到案例。"""

import json
import os
import shutil
import subprocess
from pathlib import Path

data = Path(os.environ.get("OPENMX_DATA", "DFT_DATA19")).resolve()
if not (data / "PAO").is_dir() or not (data / "VPS").is_dir():
    raise SystemExit("请设置正确的 OPENMX_DATA")
exe = shutil.which(os.environ.get("OPENMX_EXEC", "openmx"))
if not exe:
    raise SystemExit("找不到 OpenMX")
for stage in json.loads(Path("stages.json").read_text()):
    work = Path(stage)
    if work.exists():
        raise SystemExit(f"{stage} 已存在，请使用干净目录")
    work.mkdir()
    (work / "runtime.dat").write_text(
        Path(stage + ".dat").read_text().replace("@DATA_PATH@", str(data))
    )
    with (work / "openmx.out").open("w") as out:
        subprocess.run(
            [exe, "runtime.dat", "-nt", "1"],
            cwd=work,
            stdout=out,
            stderr=subprocess.STDOUT,
            check=True,
        )
