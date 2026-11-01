"""用法：OPENMX_DATA=/path/to/DFT_DATA19 python3 run.py；不复制基组与势。"""

import os
import shutil
import subprocess
from pathlib import Path

root = Path(os.environ.get("OPENMX_DATA", "DFT_DATA19")).resolve()
if not (root / "PAO").is_dir() or not (root / "VPS").is_dir():
    raise SystemExit("OPENMX_DATA 应包含 PAO 和 VPS 子目录")
if Path("openmx.out").exists():
    raise SystemExit("已有计算输出，请使用干净的案例目录")

exe = shutil.which(os.environ.get("OPENMX_EXEC", "openmx"))
if exe is None:
    raise SystemExit("找不到 OpenMX")
# 运行副本只替换数据库路径，原始教学输入保持可读。
Path("runtime.dat").write_text(
    Path("system.dat").read_text().replace("@DATA_PATH@", str(root))
)
with Path("openmx.out").open("w") as out:
    subprocess.run(
        [exe, "runtime.dat", "-nt", "1"],
        stdout=out,
        stderr=subprocess.STDOUT,
        check=True,
    )
