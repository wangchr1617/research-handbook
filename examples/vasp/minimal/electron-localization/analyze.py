"""用法：python3 analyze.py；用 Multiwfn 导出 ELF Cube，检查值域并绘制切面。"""

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import numpy as np
from ase.io.cube import read_cube


def main():
    executable = os.environ.get("MULTIWFN_EXEC")  # 可指定程序名或绝对路径。
    if not executable:
        executable = next(
            (
                name
                for name in ["Multiwfn", "Multiwfn_noGUI", "multiwfn"]
                if shutil.which(name)
            ),
            None,
        )
    if not executable:
        raise SystemExit("请安装 Multiwfn 或设置 MULTIWFN_EXEC")
    with Path("multiwfn.in").open() as commands, Path("multiwfn.log").open("w") as log:
        subprocess.run(
            [executable, "ELFCAR"],
            stdin=commands,
            stdout=log,
            stderr=subprocess.STDOUT,
            check=True,
        )
    if "cube file has been outputted" not in Path("multiwfn.log").read_text(
        errors="replace"
    ):
        raise SystemExit("未确认 Multiwfn 导出成功，请检查 multiwfn.log")
    with Path("elf.cub").open() as stream:
        data = read_cube(stream)["data"]
    if not np.isfinite(data).all() or data.min() < -1e-5 or data.max() > 1.00001:
        raise SystemExit("ELF 值域异常，请核对文件类型与转换步骤")
    result = {
        "grid_shape": list(data.shape),
        "minimum": float(data.min()),
        "maximum": float(data.max()),
        "unit": "dimensionless",
    }
    Path("elf-analysis.json").write_text(json.dumps(result, indent=2) + "\n")
    subprocess.run(
        [sys.executable, str(Path(__file__).with_name("plot.py"))], check=True
    )
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
